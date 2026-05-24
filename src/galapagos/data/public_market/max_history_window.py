from __future__ import annotations

import json
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.data.public_market.ingestion import normalize_binance_klines
from galapagos.data.public_market.max_history_discovery import (
    DISCOVERY_JSON_PATH_V5_0,
    DISCOVERY_MD_PATH_V5_0,
    VERSION_V5_0,
    build_discovery_markdown_v5_0,
    build_public_archive_url_v5_0,
    build_raw_file_inventory_entry_v5_0,
    count_binance_kline_zip_rows_fast_v5_0,
    dates_from_discovery_v5_0,
    discover_max_history_public_market_data_v5_0,
    expected_rows_from_days_v5_0,
    load_discovery_v5_0,
    raw_zip_path_v5_0,
)
from galapagos.data.public_market.max_history_window_quality import (
    TIMEFRAMES_V5_0,
    assess_max_history_timeframe,
    resample_max_history_ohlcv,
)
from galapagos.data.public_market.provenance import sha256_file, utc_now_iso
from galapagos.data.public_market.schemas import OHLCV_COLUMNS
from galapagos.data.public_market.sources.binance_archive import download_public_archive, parse_binance_kline_zip
from galapagos.data.public_market.storage import write_parquet


MANIFEST_PATH_V5_0 = Path("reports/manifests/max_history_public_market_data_v5_0_manifest.json")
REPORT_JSON_PATH_V5_0 = Path("reports/data_quality/max_history_public_market_data_v5_0.json")
REPORT_MD_PATH_V5_0 = Path("reports/data_quality/max_history_public_market_data_v5_0.md")
DOC_PATH_V5_0 = Path("docs/max_history_public_market_data_v5_0.md")
EXPECTED_LIMITATIONS_V5_0 = [
    "V5.0 etend uniquement les donnees marche publiques BTCUSDT sur l'historique maximum disponible et documente.",
    "V5.0 ne produit aucune feature, aucun label, aucun dataset ML, aucun modele ML, aucun backtest, aucune strategie et aucun ordre.",
]


def run_max_history_public_market_data_v5_0(
    root: Path = Path("."),
    *,
    force: bool = False,
    no_network: bool = False,
    validate_project_state: bool = True,
    start_date: str | None = None,
    end_date: str | None = None,
    allow_documented_gaps: bool = False,
) -> dict[str, Any]:
    root = root.resolve()
    if validate_project_state:
        _validate_project_state(root)
    discovery = _load_or_run_discovery(
        root,
        no_network=no_network,
        start_date=start_date,
        end_date=end_date,
        allow_documented_gaps=allow_documented_gaps,
    )
    if discovery.get("status") != "PASS":
        raise RuntimeError(f"V5.0 discovery must pass before run: {discovery.get('errors')}")

    dates = dates_from_discovery_v5_0(discovery)
    created_at = utc_now_iso()
    run_id = f"v5_0_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"

    _ensure_raw_archives(root, dates, force=force, no_network=no_network)
    raw_row_counts = {
        current_date: count_binance_kline_zip_rows_fast_v5_0(raw_zip_path_v5_0(root, current_date))
        for current_date in dates
    }

    selected_dates, incomplete_dates = _select_complete_contiguous_window(raw_row_counts)
    if not selected_dates:
        raise RuntimeError("no complete contiguous V5.0 raw window could be selected")
    if selected_dates != dates:
        discovery = _rewrite_discovery_for_complete_window(root, discovery, selected_dates, incomplete_dates)
        dates = selected_dates
    expected_rows = expected_rows_from_days_v5_0(len(dates))

    raw_files: dict[str, dict[str, Any]] = {}
    frames: list[pd.DataFrame] = []
    for current_date in dates:
        raw_path = raw_zip_path_v5_0(root, current_date)
        raw_sha = sha256_file(raw_path)
        raw_frame = parse_binance_kline_zip(raw_path)
        normalized = normalize_binance_klines(
            raw_frame,
            config=_normalization_config(root, current_date),
            raw_sha=raw_sha,
            ingestion_run_id=run_id,
            ingested_at_ts=created_at,
        )
        raw_files[current_date] = build_raw_file_inventory_entry_v5_0(root, current_date, rows=len(raw_frame))
        frames.append(normalized[OHLCV_COLUMNS])

    frame_1m = pd.concat(frames, ignore_index=True).sort_values("event_ts").reset_index(drop=True)
    frames_by_timeframe: dict[str, pd.DataFrame] = {"1m": frame_1m}
    for timeframe in ["5m", "15m", "1h"]:
        frame = resample_max_history_ohlcv(frame_1m, target_timeframe=timeframe)
        if len(frame) != expected_rows[timeframe]:
            raise RuntimeError(f"resampled {timeframe} rows {len(frame)} != expected {expected_rows[timeframe]}")
        frames_by_timeframe[timeframe] = frame

    outputs: dict[str, dict[str, Any]] = {}
    for timeframe, frame in frames_by_timeframe.items():
        path = output_path(root, timeframe, discovery["window_start"], discovery["window_end"])
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
        quality[timeframe] = assess_max_history_timeframe(
            frame,
            timeframe=timeframe,
            expected_rows=expected_rows[timeframe],
            window_start=discovery["window_start"],
            window_end=discovery["window_end"],
            parent_child_consistency=True,
        )

    status = "PASS" if not any(payload["errors"] for payload in quality.values()) else "FAIL"
    manifest = {
        "version": VERSION_V5_0,
        "status": status,
        "created_at_utc": created_at,
        "run_id": run_id,
        "discovery": {
            "first_available_date": discovery["first_available_date"],
            "last_available_date": discovery["last_available_date"],
            "window_start": discovery["window_start"],
            "window_end": discovery["window_end"],
            "total_days": discovery["total_days"],
            "expected_raw_files": discovery["expected_raw_files"],
            "missing_dates": discovery["missing_dates"],
            "documented_gaps_allowed": discovery["documented_gaps_allowed"],
        },
        "source": {
            "name": "binance_public_archive",
            "venue": "binance",
            "market_type": "spot",
            "symbol": "BTCUSDT",
            "source_timeframe": "1m",
        },
        "raw_files": raw_files,
        "outputs": outputs,
        "expected_rows": expected_rows,
        "quality": quality,
        "safety": _safety(),
        "limitations": EXPECTED_LIMITATIONS_V5_0,
    }
    _write_json(root / MANIFEST_PATH_V5_0, manifest)
    _write_json(root / REPORT_JSON_PATH_V5_0, dict(manifest))
    markdown = build_max_history_public_market_data_markdown_v5_0(manifest)
    _write_text(root / REPORT_MD_PATH_V5_0, markdown)
    _write_text(root / DOC_PATH_V5_0, markdown)
    _update_project_state(root, manifest)
    return manifest


def output_path(root: Path, timeframe: str, window_start: str | None = None, window_end: str | None = None) -> Path:
    if window_start is None or window_end is None:
        manifest_path = root.resolve() / MANIFEST_PATH_V5_0
        if not manifest_path.exists():
            discovery = load_discovery_v5_0(root)
            window_start = discovery["window_start"]
            window_end = discovery["window_end"]
        else:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            window_start = manifest["discovery"]["window_start"]
            window_end = manifest["discovery"]["window_end"]
    return (
        root
        / "data/research/v5_0/silver/ohlcv"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={window_start}_{window_end}"
        / "ohlcv.parquet"
    )


def build_max_history_public_market_data_markdown_v5_0(manifest: dict[str, Any]) -> str:
    discovery = manifest["discovery"]
    rows = "\n".join(
        f"- {timeframe}: `{manifest['outputs'][timeframe]['rows']}` lignes, checksum `{manifest['outputs'][timeframe]['sha256']}`"
        for timeframe in TIMEFRAMES_V5_0
    )
    quality_rows = "\n".join(
        f"- {timeframe}: gaps `{payload['gap_count']}`, doublons `{payload['duplicate_rows']}`, parent-child `{payload['parent_child_consistency']}`"
        for timeframe, payload in manifest["quality"].items()
    )
    limitations = "\n".join(f"- {item}" for item in manifest["limitations"])
    return f"""# Max Historical Public Market Data V5.0

## Objectif

V5.0 etend les donnees marche publiques BTCUSDT 1m sur l'historique maximum complet disponible et documente. La fenetre retenue est `{discovery['window_start']}` -> `{discovery['window_end']}`, soit `{discovery['total_days']}` jours.

## Source

- Source : `binance_public_archive`
- Venue : `binance`
- Market type : `spot`
- Symbole : `BTCUSDT`
- Timeframe source : `1m`
- Fenetre : `{discovery['window_start']}` -> `{discovery['window_end']}`
- Run : `{manifest['run_id']}`
- Premiere date disponible brute : `{discovery['first_available_date']}`
- Derniere date disponible brute : `{discovery['last_available_date']}`
- Dates manquantes : `{len(discovery['missing_dates'])}`

## Outputs

{rows}

## Qualite

{quality_rows}

## Limitations

{limitations}

## Securite

V5.0 ne valide aucune strategie.
V5.0 ne produit aucune feature.
V5.0 ne produit aucun label.
V5.0 ne produit aucun dataset ML.
V5.0 ne produit aucun modele ML.
V5.0 ne produit aucun backtest.
V5.0 ne produit aucun signal de trading.
V5.0 ne produit aucun ordre.
V5.0 n'autorise aucun paper live.
V5.0 n'autorise aucun trading reel.
"""


def _load_or_run_discovery(
    root: Path,
    *,
    no_network: bool,
    start_date: str | None,
    end_date: str | None,
    allow_documented_gaps: bool,
) -> dict[str, Any]:
    discovery_path = root / DISCOVERY_JSON_PATH_V5_0
    if no_network and discovery_path.exists() and start_date is None and end_date is None:
        return load_discovery_v5_0(root)
    return discover_max_history_public_market_data_v5_0(
        root,
        no_network=no_network,
        start_date=start_date,
        end_date=end_date,
        allow_documented_gaps=allow_documented_gaps,
    )


def _validate_project_state(root: Path) -> None:
    state_path = root / "reports/PROJECT_STATE.json"
    summary_path = root / "reports/current/latest_summary.md"
    state_text = state_path.read_text(encoding="utf-8") if state_path.exists() else ""
    summary_text = summary_path.read_text(encoding="utf-8") if summary_path.exists() else ""
    state = json.loads(state_text) if state_text else {}
    if state.get("last_validated_version") != "V4.8" and state.get("candidate_version") != "V4.8" and "V4.8" not in summary_text:
        raise RuntimeError("V5.0 requires V4.8 to be documented as the latest validated or candidate research gate.")


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


def _ensure_raw_archives(root: Path, dates: list[str], *, force: bool, no_network: bool) -> None:
    missing: list[str] = []
    for current_date in dates:
        raw_path = raw_zip_path_v5_0(root, current_date)
        if force and raw_path.exists():
            raw_path.unlink()
        if not raw_path.exists():
            missing.append(current_date)
    if not missing:
        return
    if no_network:
        first_missing = raw_zip_path_v5_0(root, missing[0]).relative_to(root)
        raise FileNotFoundError(f"missing raw public archive: {first_missing}")
    errors: list[str] = []
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {
            executor.submit(
                download_public_archive,
                build_public_archive_url_v5_0(current_date),
                raw_zip_path_v5_0(root, current_date),
            ): current_date
            for current_date in missing
        }
        for future in as_completed(futures):
            current_date = futures[future]
            try:
                future.result()
            except Exception as exc:
                errors.append(f"{current_date}: {exc}")
    if errors:
        raise RuntimeError(f"V5.0 raw public archive download failed: {errors[:10]}")


def _select_complete_contiguous_window(row_counts: dict[str, int]) -> tuple[list[str], list[str]]:
    complete_dates = sorted(current_date for current_date, rows in row_counts.items() if rows == 1440)
    incomplete_dates = sorted(current_date for current_date, rows in row_counts.items() if rows != 1440)
    if not complete_dates:
        return [], incomplete_dates
    runs: list[list[str]] = []
    current_run: list[str] = []
    previous: pd.Timestamp | None = None
    for current_date in complete_dates:
        current_ts = pd.Timestamp(current_date)
        if previous is None or current_ts - previous == pd.Timedelta(days=1):
            current_run.append(current_date)
        else:
            runs.append(current_run)
            current_run = [current_date]
        previous = current_ts
    runs.append(current_run)
    runs.sort(key=lambda values: (len(values), values[-1]), reverse=True)
    return runs[0], incomplete_dates


def _rewrite_discovery_for_complete_window(
    root: Path,
    discovery: dict[str, Any],
    selected_dates: list[str],
    incomplete_dates: list[str],
) -> dict[str, Any]:
    rewritten = dict(discovery)
    rewritten["window_start"] = selected_dates[0]
    rewritten["window_end"] = selected_dates[-1]
    rewritten["total_days"] = len(selected_dates)
    rewritten["expected_raw_files"] = len(selected_dates)
    rewritten["missing_dates"] = []
    rewritten["retained_dates_preview"] = {"first_5": selected_dates[:5], "last_5": selected_dates[-5:]}
    rewritten["incomplete_dates_excluded"] = incomplete_dates
    rewritten["warnings"] = sorted(
        set(
            list(rewritten.get("warnings", []))
            + [
                "V5.0 selected the longest complete contiguous raw window after excluding incomplete daily archives."
            ]
        )
    )
    rewritten["status"] = "PASS"
    _write_json(root / DISCOVERY_JSON_PATH_V5_0, rewritten)
    _write_text(root / DISCOVERY_MD_PATH_V5_0, build_discovery_markdown_v5_0(rewritten))
    return rewritten


def _update_project_state(root: Path, manifest: dict[str, Any]) -> None:
    state_path = root / "reports/PROJECT_STATE.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    state.update(
        {
            "last_validated_version": "V4.8",
            "candidate_version": "V5.0",
            "candidate_status": "pending_external_audit",
            "direction": "max historical OHLCV public market data expansion",
            "v5_0_candidate": True,
            "max_history_public_market_data_v5_0_created": True,
            "max_history_window_start_v5_0": manifest["discovery"]["window_start"],
            "max_history_window_end_v5_0": manifest["discovery"]["window_end"],
            "max_history_days_v5_0": manifest["discovery"]["total_days"],
            "max_history_ohlcv_rows_v5_0": manifest["expected_rows"],
            "raw_zip_days_v5_0": len(manifest["raw_files"]),
            "features_v5_0_created": False,
            "labels_v5_0_created": False,
            "dataset_v5_0_created": False,
            "ml_v5_0_created": False,
            "model_v5_0_created": False,
            "backtest_v5_0_created": False,
            "strategy_v5_0_created": False,
            "signal_v5_0_created": False,
            "orders_v5_0_created": False,
            "paper_live_v5_0_created": False,
            "trading_v5_0_created": False,
            "backtest_enabled": False,
            "strategy_enabled": False,
            "paper_live_enabled": False,
            "orders_enabled": False,
            "trading_enabled": False,
            "api_key_used": False,
            "private_endpoint_used": False,
            "authentication_used": False,
        }
    )
    _write_json(state_path, state)
    _write_json(root / "reports/current/latest_metrics.json", _build_latest_metrics(manifest, state))
    _write_text(root / "reports/PROJECT_STATE.md", _build_project_state_markdown(manifest))
    _write_text(root / "reports/current/latest_metrics.md", _build_latest_metrics_markdown(manifest))
    _write_text(root / "reports/current/latest_summary.md", _build_latest_summary_markdown(manifest))


def _build_latest_metrics(manifest: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    return {
        "last_validated_version": "V4.8",
        "candidate_version": "V5.0",
        "candidate_status": "pending_external_audit",
        "direction": state["direction"],
        "max_history_window_start_v5_0": manifest["discovery"]["window_start"],
        "max_history_window_end_v5_0": manifest["discovery"]["window_end"],
        "max_history_days_v5_0": manifest["discovery"]["total_days"],
        "max_history_ohlcv_rows_v5_0": manifest["expected_rows"],
        "raw_zip_days_v5_0": len(manifest["raw_files"]),
        "features_v5_0_created": False,
        "labels_v5_0_created": False,
        "dataset_v5_0_created": False,
        "ml_v5_0_created": False,
        "model_v5_0_created": False,
        "backtest_v5_0_created": False,
        "strategy_v5_0_created": False,
        "signal_v5_0_created": False,
        "orders_v5_0_created": False,
        "paper_live_v5_0_created": False,
        "trading_enabled": False,
        "paper_live_enabled": False,
        "orders_enabled": False,
        "backtest_enabled": False,
        "strategy_enabled": False,
        "api_key_used": False,
        "private_endpoint_used": False,
        "authentication_used": False,
        "external_validation_required": True,
    }


def _build_project_state_markdown(manifest: dict[str, Any]) -> str:
    return f"""# Etat du Projet : V4.8 validee localement + candidat V5.0

- **Derniere version validee** : V4.8.
- **Version candidate** : V5.0.
- **Statut candidate** : `pending_external_audit`.
- **Direction suivante** : max historical OHLCV public market data expansion.

## Candidat V5.0

- Fenetre historique retenue : `{manifest['discovery']['window_start']}` -> `{manifest['discovery']['window_end']}`.
- Nombre de jours : `{manifest['discovery']['total_days']}`.
- Row counts OHLCV : `{manifest['expected_rows']}`.
- Raw zips representes : `{len(manifest['raw_files'])}`.
- V5.0 ne cree aucune feature, aucun label, aucun dataset ML et aucun modele ML.
- V5.0 reste candidate `pending_external_audit`.

## Clause De Securite

- Aucun trading reel.
- Aucun paper live.
- Aucun ordre.
- Aucun backtest.
- Aucune strategie.
- Aucun signal de trading.
- Aucune API privee.
- Aucune cle API.
- V5.0 reste non validee avant audit externe.
"""


def _build_latest_metrics_markdown(manifest: dict[str, Any]) -> str:
    rows = "\n".join(f"- {timeframe}: `{rows}`" for timeframe, rows in manifest["expected_rows"].items())
    return f"""# Latest Metrics V5.0

- Derniere version validee : V4.8.
- Candidate : V5.0.
- Statut : `pending_external_audit`.
- Direction : max historical OHLCV public market data expansion.
- Fenetre : `{manifest['discovery']['window_start']}` -> `{manifest['discovery']['window_end']}`.
- Total jours : `{manifest['discovery']['total_days']}`.

## Row counts OHLCV

{rows}

Aucune feature V5.0, aucun label V5.0, aucun dataset ML V5.0, aucun modele ML V5.0, aucun backtest, aucune strategie, aucun ordre et aucun trading reel.
"""


def _build_latest_summary_markdown(manifest: dict[str, Any]) -> str:
    return f"""# Latest Summary V5.0

V4.8 est la derniere version validee localement.

V5.0 est la candidate courante. Elle produit uniquement une expansion OHLCV publique BTCUSDT sur l'historique maximum complet disponible, sans feature, sans label, sans dataset ML, sans modele ML et sans backtest.

Fenetre retenue : `{manifest['discovery']['window_start']}` -> `{manifest['discovery']['window_end']}`.

Total jours : `{manifest['discovery']['total_days']}`.

Row counts attendus : `{manifest['expected_rows']}`.

Aucun trading, aucun paper live, aucun ordre, aucun backtest, aucune strategie, aucun signal de trading et aucun claim de rentabilite.

V5.0 reste `pending_external_audit`.
"""


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
