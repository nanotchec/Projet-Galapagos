from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.data.public_market.ingestion import normalize_binance_klines
from galapagos.data.public_market.multi_day_quality import (
    EXPECTED_ROWS_V2_9,
    assess_multi_day_timeframe,
    parent_child_consistent,
    resample_multi_day_ohlcv,
)
from galapagos.data.public_market.provenance import sha256_file, utc_now_iso
from galapagos.data.public_market.schemas import OHLCV_COLUMNS
from galapagos.data.public_market.sources.binance_archive import (
    build_public_archive_url,
    download_public_archive,
    parse_binance_kline_zip,
)
from galapagos.data.public_market.storage import write_parquet
from galapagos.validation.market_data import validate_public_market_ingestion_v2_3


VERSION = "V2.9"
WINDOW_START = "2024-01-15"
WINDOW_END = "2024-01-21"
WINDOW_LABEL = f"{WINDOW_START}_{WINDOW_END}"
DATES_V2_9 = [
    "2024-01-15",
    "2024-01-16",
    "2024-01-17",
    "2024-01-18",
    "2024-01-19",
    "2024-01-20",
    "2024-01-21",
]
TIMEFRAMES_V2_9 = ["1m", "5m", "15m", "1h"]
EXPECTED_LIMITATIONS_V2_9 = [
    "V2.9 etend uniquement les donnees marche publiques BTCUSDT sur une fenetre fixe de 7 jours.",
    "V2.9 ne produit aucune feature, aucun label, aucun dataset ML, aucun modele ML, aucun backtest, aucune strategie et aucun ordre.",
]
MANIFEST_PATH = Path("reports/manifests/multi_day_public_market_data_v2_9_manifest.json")
REPORT_JSON_PATH = Path("reports/data_quality/multi_day_public_market_data_v2_9.json")
REPORT_MD_PATH = Path("reports/data_quality/multi_day_public_market_data_v2_9.md")


def run_multi_day_public_market_data_v2_9(
    root: Path = Path("."),
    *,
    force: bool = False,
    no_network: bool = False,
    validate_previous_layers: bool = True,
) -> dict[str, Any]:
    root = root.resolve()
    if validate_previous_layers:
        _validate_previous_layers(root)
    created_at = utc_now_iso()
    run_id = f"v2_9_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    raw_files: dict[str, dict[str, Any]] = {}
    frames: list[pd.DataFrame] = []
    for date in DATES_V2_9:
        raw_path = raw_zip_path(root, date)
        if force and raw_path.exists():
            raw_path.unlink()
        if not raw_path.exists():
            if no_network:
                raise FileNotFoundError(f"missing raw public archive: {raw_path.relative_to(root)}")
            url = build_public_archive_url(market_type="spot", symbol="BTCUSDT", timeframe="1m", date=date)
            download_public_archive(url, raw_path)
        raw_sha = sha256_file(raw_path)
        raw_frame = parse_binance_kline_zip(raw_path)
        normalized = normalize_binance_klines(
            raw_frame,
            config=_normalization_config(root, date),
            raw_sha=raw_sha,
            ingestion_run_id=run_id,
            ingested_at_ts=created_at,
        )
        raw_files[date] = {
            "path": str(raw_path.relative_to(root)),
            "sha256": raw_sha,
            "bytes": raw_path.stat().st_size,
            "rows": int(len(raw_frame)),
        }
        frames.append(normalized[OHLCV_COLUMNS])

    frame_1m = pd.concat(frames, ignore_index=True).sort_values("event_ts").reset_index(drop=True)
    outputs: dict[str, dict[str, Any]] = {}
    frames_by_timeframe: dict[str, pd.DataFrame] = {"1m": frame_1m}
    for timeframe in ["5m", "15m", "1h"]:
        frames_by_timeframe[timeframe] = resample_multi_day_ohlcv(frame_1m, target_timeframe=timeframe)
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
        quality[timeframe] = assess_multi_day_timeframe(
            frame,
            timeframe=timeframe,
            parent_child_consistency=True if timeframe == "1m" else parent_child_consistent(frame_1m, frame, timeframe),
        )
    status = "PASS" if not any(payload["errors"] for payload in quality.values()) else "FAIL"
    manifest = {
        "version": VERSION,
        "status": status,
        "created_at_utc": created_at,
        "run_id": run_id,
        "source": {
            "name": "binance_public_archive",
            "venue": "binance",
            "market_type": "spot",
            "symbol": "BTCUSDT",
            "source_timeframe": "1m",
            "window_start": WINDOW_START,
            "window_end": WINDOW_END,
        },
        "raw_files": raw_files,
        "outputs": outputs,
        "expected_rows": EXPECTED_ROWS_V2_9,
        "quality": quality,
        "safety": _safety(),
        "limitations": EXPECTED_LIMITATIONS_V2_9,
    }
    report = dict(manifest)
    _write_json(root / MANIFEST_PATH, manifest)
    _write_json(root / REPORT_JSON_PATH, report)
    _write_markdown(root / REPORT_MD_PATH, report)
    return manifest


def raw_zip_path(root: Path, date: str) -> Path:
    return root / "data/raw/public_market/binance_archive/spot/BTCUSDT/klines/1m" / f"BTCUSDT-1m-{date}.zip"


def output_path(root: Path, timeframe: str) -> Path:
    return (
        root
        / "data/research/v2_9/silver/ohlcv"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={WINDOW_LABEL}"
        / "ohlcv.parquet"
    )


def _validate_previous_layers(root: Path) -> None:
    validation = validate_public_market_ingestion_v2_3(root)
    if not validation["passed"]:
        raise RuntimeError(f"V2.3.1 validation failed before V2.9: {validation['errors']}")
    from galapagos.datasets.validation import validate_offline_supervised_dataset_v2_7
    from galapagos.features.validation import validate_causal_feature_store_v2_5
    from galapagos.labels.validation import validate_label_factory_v2_6
    from galapagos.ml.validation import validate_offline_ml_research_v2_8
    from galapagos.validation.resampling import validate_ohlcv_resampling_v2_4

    for label, validator in [
        ("V2.4.8", validate_ohlcv_resampling_v2_4),
        ("V2.5.2", validate_causal_feature_store_v2_5),
        ("V2.6.2", validate_label_factory_v2_6),
        ("V2.7.2", validate_offline_supervised_dataset_v2_7),
        ("V2.8.4", validate_offline_ml_research_v2_8),
    ]:
        result = validator(root)
        if not result["passed"]:
            raise RuntimeError(f"{label} validation failed before V2.9: {result['errors']}")


def _normalization_config(root: Path, date: str) -> Any:
    class _Config:
        source = "binance_archive"
        market_type = "spot"
        symbol = "BTCUSDT"
        timeframe = "1m"
        output_root = root
        force = False
        no_network = False
        fail_on_quality_warning = False

        def __init__(self, date: str) -> None:
            self.date = date

    return _Config(date)


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


def _write_markdown(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = "\n".join(
        f"- {timeframe}: `{report['outputs'][timeframe]['rows']}` lignes, checksum `{report['outputs'][timeframe]['sha256']}`"
        for timeframe in TIMEFRAMES_V2_9
    )
    raw_rows = "\n".join(
        f"- {date}: `{payload['rows']}` lignes, `{payload['path']}`, checksum `{payload['sha256']}`"
        for date, payload in report["raw_files"].items()
    )
    quality_rows = "\n".join(
        f"- {timeframe}: gaps `{payload['gap_count']}`, doublons `{payload['duplicate_rows']}`, parent-child `{payload['parent_child_consistency']}`"
        for timeframe, payload in report["quality"].items()
    )
    limitations = "\n".join(f"- {item}" for item in report["limitations"])
    text = f"""# Multi-Day Public Market Data V2.9

## Objectif

V2.9 etend les donnees marche publiques BTCUSDT 1m sur une fenetre fixe de 7 jours, du {WINDOW_START} au {WINDOW_END}.

## Source

- Source : `binance_public_archive`
- Venue : `binance`
- Market type : `spot`
- Symbole : `BTCUSDT`
- Timeframe source : `1m`
- Fenetre : `{WINDOW_START}` -> `{WINDOW_END}`
- Run : `{report['run_id']}`

## Fichiers raw

{raw_rows}

## Outputs

{rows}

## Qualite

{quality_rows}

## Limitations

{limitations}

## Securite

V2.9 ne valide aucune strategie.
V2.9 ne produit aucune feature.
V2.9 ne produit aucun label.
V2.9 ne produit aucun dataset ML.
V2.9 ne produit aucun modele ML.
V2.9 ne produit aucun backtest.
V2.9 ne produit aucun signal de trading.
V2.9 ne produit aucun ordre.
V2.9 n'autorise aucun paper live.
V2.9 n'autorise aucun trading reel.
"""
    path.write_text(text, encoding="utf-8")
