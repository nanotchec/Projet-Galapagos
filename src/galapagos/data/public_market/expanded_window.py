from __future__ import annotations

import json
import uuid
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.data.public_market.expanded_window_quality import (
    EXPECTED_ROWS_V3_5,
    assess_expanded_timeframe,
    resample_expanded_ohlcv,
)
from galapagos.data.public_market.ingestion import normalize_binance_klines
from galapagos.data.public_market.provenance import sha256_file, utc_now_iso
from galapagos.data.public_market.schemas import OHLCV_COLUMNS
from galapagos.data.public_market.sources.binance_archive import (
    build_public_archive_url,
    download_public_archive,
    parse_binance_kline_zip,
)
from galapagos.data.public_market.storage import write_parquet


VERSION_V3_5 = "V3.5"
WINDOW_START_V3_5 = "2024-01-01"
WINDOW_END_V3_5 = "2024-03-30"
WINDOW_LABEL_V3_5 = f"{WINDOW_START_V3_5}_{WINDOW_END_V3_5}"
TIMEFRAMES_V3_5 = ["1m", "5m", "15m", "1h"]
DATES_V3_5 = [
    (date.fromisoformat(WINDOW_START_V3_5) + timedelta(days=offset)).isoformat()
    for offset in range((date.fromisoformat(WINDOW_END_V3_5) - date.fromisoformat(WINDOW_START_V3_5)).days + 1)
]
EXPECTED_LIMITATIONS_V3_5 = [
    "V3.5 etend uniquement les donnees marche publiques BTCUSDT sur une fenetre fixe de 90 jours.",
    "V3.5 ne produit aucune feature, aucun label, aucun dataset ML, aucun modele ML, aucun backtest, aucune strategie et aucun ordre.",
]
MANIFEST_PATH_V3_5 = Path("reports/manifests/expanded_public_market_data_v3_5_manifest.json")
REPORT_JSON_PATH_V3_5 = Path("reports/data_quality/expanded_public_market_data_v3_5.json")
REPORT_MD_PATH_V3_5 = Path("reports/data_quality/expanded_public_market_data_v3_5.md")
DOC_PATH_V3_5 = Path("docs/expanded_public_market_data_v3_5.md")


def run_expanded_public_market_data_v3_5(
    root: Path = Path("."),
    *,
    force: bool = False,
    no_network: bool = False,
    validate_project_state: bool = True,
) -> dict[str, Any]:
    root = root.resolve()
    if validate_project_state:
        _validate_project_state(root)
    created_at = utc_now_iso()
    run_id = f"v3_5_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    raw_files: dict[str, dict[str, Any]] = {}
    frames: list[pd.DataFrame] = []

    for current_date in DATES_V3_5:
        raw_path = raw_zip_path(root, current_date)
        if force and raw_path.exists():
            raw_path.unlink()
        if not raw_path.exists():
            if no_network:
                raise FileNotFoundError(f"missing raw public archive: {raw_path.relative_to(root)}")
            url = build_public_archive_url(market_type="spot", symbol="BTCUSDT", timeframe="1m", date=current_date)
            download_public_archive(url, raw_path)
        raw_sha = sha256_file(raw_path)
        raw_frame = parse_binance_kline_zip(raw_path)
        normalized = normalize_binance_klines(
            raw_frame,
            config=_normalization_config(root, current_date),
            raw_sha=raw_sha,
            ingestion_run_id=run_id,
            ingested_at_ts=created_at,
        )
        raw_files[current_date] = {
            "path": str(raw_path.relative_to(root)),
            "sha256": raw_sha,
            "bytes": raw_path.stat().st_size,
            "rows": int(len(raw_frame)),
        }
        frames.append(normalized[OHLCV_COLUMNS])

    frame_1m = pd.concat(frames, ignore_index=True).sort_values("event_ts").reset_index(drop=True)
    frames_by_timeframe: dict[str, pd.DataFrame] = {"1m": frame_1m}
    for timeframe in ["5m", "15m", "1h"]:
        frames_by_timeframe[timeframe] = resample_expanded_ohlcv(frame_1m, target_timeframe=timeframe)

    outputs: dict[str, dict[str, Any]] = {}
    for timeframe, frame in frames_by_timeframe.items():
        path = output_path(root, timeframe)
        write_parquet(frame[OHLCV_COLUMNS], path)
        outputs[timeframe] = {
            "path": str(path.relative_to(root)),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
            "rows": int(len(frame)),
            "format": "parquet",
        }

    quality: dict[str, dict[str, Any]] = {}
    for timeframe, frame in frames_by_timeframe.items():
        quality[timeframe] = assess_expanded_timeframe(
            frame,
            timeframe=timeframe,
            parent_child_consistency=True,
        )

    status = "PASS" if not any(payload["errors"] for payload in quality.values()) else "FAIL"
    manifest = {
        "version": VERSION_V3_5,
        "status": status,
        "created_at_utc": created_at,
        "run_id": run_id,
        "source": {
            "name": "binance_public_archive",
            "venue": "binance",
            "market_type": "spot",
            "symbol": "BTCUSDT",
            "source_timeframe": "1m",
            "window_start": WINDOW_START_V3_5,
            "window_end": WINDOW_END_V3_5,
        },
        "raw_files": raw_files,
        "outputs": outputs,
        "expected_rows": EXPECTED_ROWS_V3_5,
        "quality": quality,
        "safety": _safety(),
        "limitations": EXPECTED_LIMITATIONS_V3_5,
    }
    _write_json(root / MANIFEST_PATH_V3_5, manifest)
    _write_json(root / REPORT_JSON_PATH_V3_5, dict(manifest))
    markdown = build_expanded_public_market_data_markdown_v3_5(manifest)
    _write_text(root / REPORT_MD_PATH_V3_5, markdown)
    _write_text(root / DOC_PATH_V3_5, markdown)
    return manifest


def raw_zip_path(root: Path, current_date: str) -> Path:
    return root / "data/raw/public_market/binance_archive/spot/BTCUSDT/klines/1m" / f"BTCUSDT-1m-{current_date}.zip"


def output_path(root: Path, timeframe: str) -> Path:
    return (
        root
        / "data/research/v3_5/silver/ohlcv"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={WINDOW_LABEL_V3_5}"
        / "ohlcv.parquet"
    )


def build_expanded_public_market_data_markdown_v3_5(manifest: dict[str, Any]) -> str:
    rows = "\n".join(
        f"- {timeframe}: `{manifest['outputs'][timeframe]['rows']}` lignes, checksum `{manifest['outputs'][timeframe]['sha256']}`"
        for timeframe in TIMEFRAMES_V3_5
    )
    quality_rows = "\n".join(
        f"- {timeframe}: gaps `{payload['gap_count']}`, doublons `{payload['duplicate_rows']}`, parent-child `{payload['parent_child_consistency']}`"
        for timeframe, payload in manifest["quality"].items()
    )
    limitations = "\n".join(f"- {item}" for item in manifest["limitations"])
    return f"""# Expanded Public Market Data V3.5

Note V3.5.1 : correction strictement runtime et ZIP completeness. Les donnees OHLCV V3.5 restent identiques ; V3.5.1 rend le ZIP auto-testable et accelere run/validate/smoke/tests sans creer de features, labels, dataset ML, ML, backtest, strategie ou ordre.

## Objectif

V3.5 etend les donnees marche publiques BTCUSDT 1m sur une fenetre fixe de 90 jours, du {WINDOW_START_V3_5} au {WINDOW_END_V3_5}.

## Source

- Source : `binance_public_archive`
- Venue : `binance`
- Market type : `spot`
- Symbole : `BTCUSDT`
- Timeframe source : `1m`
- Fenetre : `{WINDOW_START_V3_5}` -> `{WINDOW_END_V3_5}`
- Run : `{manifest['run_id']}`

## Outputs

{rows}

## Qualite

{quality_rows}

## Limitations

{limitations}

## Securite

V3.5 ne valide aucune strategie.
V3.5 ne produit aucune feature.
V3.5 ne produit aucun label.
V3.5 ne produit aucun dataset ML.
V3.5 ne produit aucun modele ML.
V3.5 ne produit aucun backtest.
V3.5 ne produit aucun signal de trading.
V3.5 ne produit aucun ordre.
V3.5 n'autorise aucun paper live.
V3.5 n'autorise aucun trading reel.
"""


def _validate_project_state(root: Path) -> None:
    state_path = root / "reports/PROJECT_STATE.json"
    summary_path = root / "reports/current/latest_summary.md"
    state_text = state_path.read_text(encoding="utf-8") if state_path.exists() else ""
    summary_text = summary_path.read_text(encoding="utf-8") if summary_path.exists() else ""
    state = json.loads(state_text) if state_text else {}
    if state.get("last_validated_version") != "V3.4.1" and "V3.4.1" not in summary_text:
        raise RuntimeError("V3.5 requires V3.4.1 to be documented as the latest externally validated version.")


def _normalization_config(root: Path, current_date: str) -> Any:
    class _Config:
        source = "binance_archive"
        market_type = "spot"
        symbol = "BTCUSDT"
        timeframe = "1m"
        output_root = root
        force = False
        no_network = False
        fail_on_quality_warning = False

        def __init__(self, selected_date: str) -> None:
            self.date = selected_date

    return _Config(current_date)


def _safety() -> dict[str, bool]:
    return {
        "public_read_only": True,
        "authentication_used": False,
        "api_key_used": False,
        "private_endpoint_used": False,
        "orders_enabled": False,
        "paper_live_enabled": False,
        "trading_enabled": False,
        "ml_enabled": False,
        "labels_enabled": False,
        "dataset_enabled": False,
        "backtest_enabled": False,
        "strategy_enabled": False,
        "execution_enabled": False,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
