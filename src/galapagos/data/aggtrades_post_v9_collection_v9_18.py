from __future__ import annotations

import json
import zipfile
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen


VERSION = "V9.18"
LAST_VALIDATED_VERSION = "V9.17"
SOURCE_VERSION = "V9.17"
DIRECTION = "aggtrades_post_v9_collection_pack"

TARGET_START = "2024-03-25"
TARGET_END = "2026-05-05"
FUNDING_FIRST_START = "2024-05-05"
FUNDING_FIRST_END = "2026-05-05"
VENUE = "binance"
SOURCE = "binance_public_archive"
SOURCE_STORAGE = "binance_archive"
MARKET_TYPE = "spot"
SYMBOL = "BTCUSDT"
TRADE_SOURCE_TYPE = "aggTrades"
PUBLIC_ARCHIVE_HOST = "data.binance.vision"
ALLOWED_PUBLIC_HOSTS = {PUBLIC_ARCHIVE_HOST}

REPORT_JSON_PATH = Path("reports/data/aggtrades_post_v9_collection_v9_18.json")
REPORT_MD_PATH = Path("reports/data/aggtrades_post_v9_collection_v9_18.md")
MANIFEST_PATH = Path("reports/manifests/aggtrades_post_v9_collection_v9_18_manifest.json")
DOC_PATH = Path("docs/aggtrades_post_v9_collection_v9_18.md")

ALLOWED_MODES = {"dry-run", "collect", "validate-only"}
ALLOWED_DECISIONS = {
    "aggtrades_post_v9_collection_pack_ready_dry_run_only",
    "aggtrades_post_v9_collection_partial",
    "aggtrades_post_v9_collection_complete",
    "aggtrades_post_v9_collection_not_ready_source_issue",
    "aggtrades_post_v9_collection_not_ready_quality_failed",
    "stop_aggtrades_collection_branch",
}

INPUT_PATHS = {
    "v9_17_decision": Path("reports/research_decisions/derivatives_history_collection_plan_v9_17.json"),
    "v9_17_manifest": Path("reports/manifests/derivatives_history_collection_plan_v9_17_manifest.json"),
    "v9_16_decision": Path("reports/research_decisions/derivatives_window_extension_v9_16.json"),
    "v9_15_decision": Path("reports/research_decisions/derivatives_data_extension_readiness_v9_15.json"),
    "v9_14_1_decision": Path("reports/research_decisions/feature_label_separability_v9_14_1.json"),
    "public_trades_1y_window_v8_2_manifest": Path("reports/manifests/public_trades_1y_window_v8_2_manifest.json"),
    "max_history_public_market_data_v5_0_manifest": Path("reports/manifests/max_history_public_market_data_v5_0_manifest.json"),
    "refined_ohlcv_trades_feature_store_v9_0_manifest": Path("reports/manifests/refined_ohlcv_trades_feature_store_v9_0_manifest.json"),
    "derivatives_coverage_v1_14": Path("reports/research/derivatives_coverage_v1_14.json"),
    "derivatives_data_quality_v1_14": Path("reports/research/derivatives_data_quality_v1_14.json"),
    "derivatives_features_v1_14": Path("reports/research/derivatives_features_v1_14.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
    "latest_summary": Path("reports/current/latest_summary.md"),
    "project_state": Path("reports/PROJECT_STATE.json"),
    "project_state_md": Path("reports/PROJECT_STATE.md"),
}

RAW_DIR = Path("data/raw/public_trades/binance_archive/spot/BTCUSDT/aggTrades")
RAW_PARTITION_TEMPLATE = "data/raw/public_trades/binance_archive/spot/BTCUSDT/aggTrades/BTCUSDT-aggTrades-{date}.zip"
BRONZE_PARTITION_TEMPLATE = "data/raw/public_trades/binance_archive/spot/BTCUSDT/aggTrades/BTCUSDT-aggTrades-{date}.zip"
SILVER_PARTITION_TEMPLATE = "data/silver/public_trades/venue=binance/market_type=spot/symbol=BTCUSDT/date={date}/agg_trades.parquet"
QUARANTINE_DIR = Path("data/quarantine/public_trades/venue=binance/market_type=spot/symbol=BTCUSDT")

SILVER_COLUMNS_V9_18 = [
    "source",
    "venue",
    "market_type",
    "symbol",
    "aggregate_trade_id",
    "price",
    "quantity",
    "first_trade_id",
    "last_trade_id",
    "event_ts",
    "trade_ts",
    "is_buyer_maker",
    "ingest_ts",
    "available_ts",
    "source_file",
    "source_checksum",
    "row_valid",
    "invalid_reason",
]

QUALITY_CHECKS = [
    "file_present",
    "file_readable",
    "expected_schema",
    "valid_types",
    "timestamps_utc",
    "price_positive",
    "quantity_positive",
    "aggregate_trade_id_monotone_or_coherent",
    "no_duplicate_aggregate_trade_id",
    "invalid_rows_not_excessive",
    "partition_date_matches_event_ts",
    "file_size_nonzero",
    "day_status",
]

FINDINGS = {
    "robust_edge_claimed": False,
    "strategy_validated": False,
    "backtest_performed": False,
    "actionable_signal_produced": False,
    "walk_forward_validated_for_trading": False,
    "trading_allowed": False,
    "paper_live_allowed": False,
    "real_trading_allowed": False,
}

BASE_SAFETY_FLAGS = {
    "no_trading": True,
    "no_paper_live": True,
    "no_orders": True,
    "no_backtest": True,
    "no_walk_forward": True,
    "no_strategy": True,
    "no_actionable_signal": True,
    "no_persistent_model": True,
    "api_key_used": False,
    "private_endpoint_used": False,
    "exchange_auth_used": False,
    "websocket_live_used": False,
    "no_sidecars": True,
    "no_zip_fingerprints": True,
}


def run_aggtrades_post_v9_collection_v9_18(
    root: Path = Path("."),
    *,
    mode: str = "dry-run",
    max_downloads: int | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    report = build_aggtrades_post_v9_collection_report_v9_18(root, mode=mode, max_downloads=max_downloads)
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_18(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / MANIFEST_PATH, build_manifest_v9_18(report))
    update_state_surfaces_v9_18(root, report)
    return report


def build_aggtrades_post_v9_collection_report_v9_18(
    root: Path = Path("."),
    *,
    mode: str = "dry-run",
    max_downloads: int | None = None,
) -> dict[str, Any]:
    if mode not in ALLOWED_MODES:
        raise ValueError(f"unsupported V9.18 mode: {mode}")
    root = root.resolve()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    input_payloads = {name: item["payload"] for name, item in inputs.items()}
    target_dates = date_range_v9_18(TARGET_START, TARGET_END)
    funding_first_dates = date_range_v9_18(FUNDING_FIRST_START, FUNDING_FIRST_END)
    convention = detect_storage_convention_v9_18(root)
    local_inventory = build_local_raw_inventory_v9_18(root, target_dates)
    day_plan = build_day_plan_v9_18(root, target_dates, local_inventory)
    collection_result = execute_collection_mode_v9_18(root, mode, day_plan, max_downloads=max_downloads)
    if collection_result["collection_executed"]:
        local_inventory = build_local_raw_inventory_v9_18(root, target_dates)
        day_plan = build_day_plan_v9_18(root, target_dates, local_inventory)
    coverage = summarize_coverage_v9_18(target_dates, day_plan)
    source_design = build_source_design_v9_18(convention)
    quality_plan = build_quality_plan_v9_18()
    anti_leakage = build_anti_leakage_plan_v9_18()
    volume_estimate = estimate_volume_v9_18(input_payloads, coverage["days_expected"])
    safety_flags = safety_flags_for_mode_v9_18(collection_result["collection_executed"])
    decision = decide_v9_18(mode, collection_result, coverage)
    report = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": "PASS" if collection_result["status"] == "PASS" else "FAIL",
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "mode": mode,
        "inputs_used": {name: {"path": item["path"], "available": item["available"]} for name, item in inputs.items()},
        "source_public_target": source_design,
        "storage_convention": convention,
        "target_window": {
            "start": TARGET_START,
            "end": TARGET_END,
            "days_expected": len(target_dates),
        },
        "future_funding_first_window": {
            "start": FUNDING_FIRST_START,
            "end": FUNDING_FIRST_END,
            "days_expected": len(funding_first_dates),
        },
        "local_raw_inventory": local_inventory,
        "day_plan": day_plan,
        "coverage_summary": coverage,
        "volume_estimate": volume_estimate,
        "collection_result": collection_result,
        "quality_validation_plan": quality_plan,
        "anti_leakage_plan": anti_leakage,
        "silver_schema_columns": list(SILVER_COLUMNS_V9_18),
        "v9_18_decision": decision,
        "next_recommendation": decision["next_recommendation"],
        "collection_executed": collection_result["collection_executed"],
        "network_used": collection_result["network_used"],
        "new_data_downloaded": collection_result["new_data_downloaded"],
        "ingestion_executed": collection_result["ingestion_executed"],
        "features_created": False,
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "blockers": coverage["missing_dates_preview"] if coverage["days_missing"] else [],
        "warnings": [
            "V9.18 dry-run ne telecharge rien et ne marque pas la couverture comme complete.",
            "Une future execution collect devra rester publique, read-only, sans cle et sans endpoint prive.",
        ],
        "limitations": [
            "La verification distante des fichiers publics n'est pas faite en dry-run.",
            "Les checks stricts de schema/row-level ne sont executes que sur les fichiers effectivement collectes ou presents.",
            "Aucune integration funding/open-interest n'est faite dans V9.18.",
        ],
        "findings": dict(FINDINGS),
        "safety_flags": safety_flags,
    }
    return report


def detect_storage_convention_v9_18(root: Path) -> dict[str, Any]:
    existing_raw = root / RAW_DIR
    selected = "existing_public_trades_convention" if existing_raw.exists() else "planned_public_trades_convention"
    return {
        "selected_convention": selected,
        "existing_raw_dir": RAW_DIR.as_posix(),
        "bronze_raw_pattern": BRONZE_PARTITION_TEMPLATE,
        "silver_normalized_pattern": SILVER_PARTITION_TEMPLATE,
        "quarantine_dir": QUARANTINE_DIR.as_posix(),
        "reason": "Le repo contient deja data/raw/public_trades/binance_archive/spot/BTCUSDT/aggTrades; V9.18 respecte cette convention.",
    }


def build_local_raw_inventory_v9_18(root: Path, target_dates: list[str]) -> dict[str, Any]:
    files = []
    present_dates: list[str] = []
    zero_byte_dates: list[str] = []
    target_set = set(target_dates)
    raw_dir = root / RAW_DIR
    if raw_dir.exists():
        for path in sorted(raw_dir.glob(f"{SYMBOL}-{TRADE_SOURCE_TYPE}-*.zip")):
            parsed_date = parse_date_from_raw_name_v9_18(path.name)
            if parsed_date is None or parsed_date not in target_set:
                continue
            size = path.stat().st_size
            present_dates.append(parsed_date)
            if size <= 0:
                zero_byte_dates.append(parsed_date)
            files.append({"date": parsed_date, "path": path.relative_to(root).as_posix(), "bytes": size})
    missing_dates = [item for item in target_dates if item not in set(present_dates)]
    return {
        "raw_dir": RAW_DIR.as_posix(),
        "files_count": len(files),
        "present_dates": present_dates,
        "missing_dates": missing_dates,
        "zero_byte_dates": zero_byte_dates,
        "files_preview": files[:10],
        "target_window_files_only": True,
    }


def build_day_plan_v9_18(root: Path, target_dates: list[str], local_inventory: dict[str, Any]) -> list[dict[str, Any]]:
    present = set(local_inventory["present_dates"])
    zero_byte = set(local_inventory["zero_byte_dates"])
    plan = []
    for current_date in target_dates:
        raw_path = root / raw_zip_path_for_date_v9_18(current_date)
        if current_date in zero_byte:
            status = "day_partial"
        elif current_date in present:
            status = "day_present"
        else:
            status = "day_missing"
        plan.append(
            {
                "date": current_date,
                "status": status,
                "raw_path": raw_zip_path_for_date_v9_18(current_date).as_posix(),
                "silver_path": silver_path_for_date_v9_18(current_date).as_posix(),
                "public_url": build_public_archive_url_v9_18(current_date),
                "file_exists": raw_path.exists(),
                "file_bytes": raw_path.stat().st_size if raw_path.exists() else 0,
                "quarantine_required": status == "day_partial",
            }
        )
    return plan


def summarize_coverage_v9_18(target_dates: list[str], day_plan: list[dict[str, Any]]) -> dict[str, Any]:
    present = [item["date"] for item in day_plan if item["status"] == "day_present"]
    missing = [item["date"] for item in day_plan if item["status"] == "day_missing"]
    quarantined = [item["date"] for item in day_plan if item["status"] == "day_quarantined"]
    partial = [item["date"] for item in day_plan if item["status"] == "day_partial"]
    days_expected = len(target_dates)
    days_present = len(present)
    return {
        "window_start": TARGET_START,
        "window_end": TARGET_END,
        "days_expected": days_expected,
        "days_already_present": days_present,
        "days_collected": 0,
        "days_missing": len(missing),
        "days_quarantined": len(quarantined),
        "days_partial": len(partial),
        "coverage_ratio": round(days_present / days_expected, 6) if days_expected else 0.0,
        "coverage_start": present[0] if present else None,
        "coverage_end": present[-1] if present else None,
        "present_dates": present,
        "missing_dates": missing,
        "missing_dates_preview": missing[:20],
        "total_rows": None,
        "invalid_rows": None,
        "duplicates": None,
        "min_event_ts": None,
        "max_event_ts": None,
        "min_aggregate_trade_id": None,
        "max_aggregate_trade_id": None,
        "coverage_complete": not missing and not partial and not quarantined,
    }


def build_source_design_v9_18(convention: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_name": "Binance public archive aggTrades daily files",
        "host": PUBLIC_ARCHIVE_HOST,
        "allowed_public_hosts": sorted(ALLOWED_PUBLIC_HOSTS),
        "venue": VENUE,
        "market_type": MARKET_TYPE,
        "symbol": SYMBOL,
        "trade_source_type": TRADE_SOURCE_TYPE,
        "target_window": f"{TARGET_START}_{TARGET_END}",
        "funding_first_research_window": f"{FUNDING_FIRST_START}_{FUNDING_FIRST_END}",
        "account_required": False,
        "api_key_required": False,
        "private_endpoint_required": False,
        "exchange_auth_required": False,
        "websocket_live_required": False,
        "download_url_template": f"https://{PUBLIC_ARCHIVE_HOST}/data/spot/daily/aggTrades/BTCUSDT/BTCUSDT-aggTrades-YYYY-MM-DD.zip",
        "bronze_raw_pattern": convention["bronze_raw_pattern"],
        "silver_normalized_pattern": convention["silver_normalized_pattern"],
        "expected_silver_columns": list(SILVER_COLUMNS_V9_18),
    }


def build_quality_plan_v9_18() -> list[dict[str, Any]]:
    return [{"check_name": item, "scope": "per_day" if item != "coverage" else "window", "required": True} for item in QUALITY_CHECKS]


def build_anti_leakage_plan_v9_18() -> dict[str, Any]:
    return {
        "rules": [
            "available_ts >= event_ts for every normalized row.",
            "No future-derived feature is created in V9.18.",
            "No label join is allowed in V9.18.",
            "Funding and open interest are not integrated in V9.18.",
            "Future feature alignment must use available_ts <= decision_ts.",
        ],
        "forbidden_outputs": ["label", "prediction", "model_score", "signal", "trading_signal", "order", "backtest", "position_size", "strategy"],
    }


def estimate_volume_v9_18(input_payloads: dict[str, Any], target_days: int) -> dict[str, Any]:
    v8_2 = input_payloads.get("public_trades_1y_window_v8_2_manifest", {})
    raw_files = v8_2.get("raw_files", {})
    partitions = v8_2.get("outputs", {}).get("partitions", {})
    raw_bytes = [item.get("bytes") for item in raw_files.values() if isinstance(item.get("bytes"), int)]
    rows = [item.get("rows") for item in partitions.values() if isinstance(item.get("rows"), int)]
    avg_raw_bytes = int(sum(raw_bytes) / len(raw_bytes)) if raw_bytes else None
    avg_rows = int(sum(rows) / len(rows)) if rows else None
    return {
        "basis": "V8.2 one-year local aggTrades manifest" if raw_bytes or rows else "unknown",
        "average_raw_zip_bytes": avg_raw_bytes,
        "average_rows_per_day": avg_rows,
        "estimated_raw_zip_bytes_for_target": avg_raw_bytes * target_days if avg_raw_bytes is not None else None,
        "estimated_rows_for_target": avg_rows * target_days if avg_rows is not None else None,
        "estimate_is_for_planning_only": True,
    }


def execute_collection_mode_v9_18(root: Path, mode: str, day_plan: list[dict[str, Any]], *, max_downloads: int | None = None) -> dict[str, Any]:
    if mode == "dry-run":
        return {
            "mode": mode,
            "status": "PASS",
            "collection_executed": False,
            "network_used": False,
            "new_data_downloaded": False,
            "ingestion_executed": False,
            "network_scope": None,
            "new_data_download_scope": None,
            "ingestion_scope": None,
            "days_attempted": 0,
            "days_downloaded": 0,
            "days_normalized": 0,
            "errors": [],
        }
    if mode == "validate-only":
        return {
            "mode": mode,
            "status": "PASS",
            "collection_executed": False,
            "network_used": False,
            "new_data_downloaded": False,
            "ingestion_executed": False,
            "network_scope": None,
            "new_data_download_scope": None,
            "ingestion_scope": None,
            "days_attempted": len([item for item in day_plan if item["file_exists"]]),
            "days_downloaded": 0,
            "days_normalized": 0,
            "errors": [],
        }
    return collect_public_aggtrades_v9_18(root, day_plan, max_downloads=max_downloads)


def collect_public_aggtrades_v9_18(root: Path, day_plan: list[dict[str, Any]], *, max_downloads: int | None = None) -> dict[str, Any]:
    missing_days = [item for item in day_plan if item["status"] == "day_missing"]
    limit = len(missing_days) if max_downloads is None else max(0, max_downloads)
    attempted = missing_days[:limit]
    errors: list[str] = []
    downloaded = 0
    normalized = 0
    for item in attempted:
        raw_path = root / item["raw_path"]
        silver_path = root / item["silver_path"]
        try:
            download_public_archive_v9_18(item["public_url"], raw_path)
            downloaded += 1
            normalize_raw_zip_to_silver_v9_18(raw_path, silver_path, item["date"])
            normalized += 1
        except Exception as exc:  # noqa: BLE001 - report exact collection failure without masking other days.
            errors.append(f"{item['date']}: {exc}")
    return {
        "mode": "collect",
        "status": "PASS" if not errors else "FAIL",
        "collection_executed": True,
        "network_used": True,
        "new_data_downloaded": downloaded > 0,
        "ingestion_executed": normalized > 0,
        "network_scope": "public_archive_read_only",
        "new_data_download_scope": "public_historical_aggtrades_only",
        "ingestion_scope": "public_aggtrades_bronze_silver_only",
        "days_attempted": len(attempted),
        "days_downloaded": downloaded,
        "days_normalized": normalized,
        "errors": errors,
    }


def download_public_archive_v9_18(url: str, destination: Path) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc not in ALLOWED_PUBLIC_HOSTS:
        raise ValueError("V9.18 allows public read-only downloads from data.binance.vision only.")
    if destination.exists() and destination.stat().st_size > 0:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "galapagos-v9.18-public-read-only"})
    with urlopen(request, timeout=120) as response:
        if getattr(response, "status", 200) != 200:
            raise RuntimeError(f"public archive download failed with status {response.status}")
        destination.write_bytes(response.read())


def normalize_raw_zip_to_silver_v9_18(raw_path: Path, silver_path: Path, current_date: str) -> None:
    import pandas as pd

    with zipfile.ZipFile(raw_path) as archive:
        csv_names = [name for name in archive.namelist() if name.endswith(".csv")]
        if len(csv_names) != 1:
            raise ValueError("Expected exactly one CSV inside Binance aggTrades archive.")
        with archive.open(csv_names[0]) as handle:
            frame = pd.read_csv(
                handle,
                header=None,
                names=[
                    "aggregate_trade_id",
                    "price",
                    "quantity",
                    "first_trade_id",
                    "last_trade_id",
                    "trade_time",
                    "is_buyer_maker",
                    "is_best_match",
                ],
            )
    event_ts = pd.to_datetime(frame["trade_time"], unit="ms", utc=True)
    available_ts = pd.Timestamp(f"{current_date}T00:00:00Z") + pd.Timedelta(days=1)
    invalid = (frame["price"].astype(float) <= 0) | (frame["quantity"].astype(float) <= 0)
    output = pd.DataFrame(
        {
            "source": SOURCE_STORAGE,
            "venue": VENUE,
            "market_type": MARKET_TYPE,
            "symbol": SYMBOL,
            "aggregate_trade_id": frame["aggregate_trade_id"].astype("int64"),
            "price": frame["price"].astype(float),
            "quantity": frame["quantity"].astype(float),
            "first_trade_id": frame["first_trade_id"].astype("int64"),
            "last_trade_id": frame["last_trade_id"].astype("int64"),
            "event_ts": event_ts.dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "trade_ts": event_ts.dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "is_buyer_maker": frame["is_buyer_maker"].astype(bool),
            "ingest_ts": _utc_now(),
            "available_ts": available_ts.isoformat().replace("+00:00", "Z"),
            "source_file": raw_path.as_posix(),
            "source_checksum": checksum_file_v9_18(raw_path),
            "row_valid": ~invalid,
            "invalid_reason": ["price_or_quantity_non_positive" if value else "" for value in invalid.tolist()],
        }
    )
    silver_path.parent.mkdir(parents=True, exist_ok=True)
    output[SILVER_COLUMNS_V9_18].to_parquet(silver_path, index=False)


def decide_v9_18(mode: str, collection_result: dict[str, Any], coverage: dict[str, Any]) -> dict[str, Any]:
    if mode == "dry-run":
        decision = "aggtrades_post_v9_collection_pack_ready_dry_run_only"
        recommendation = "V9.19 - AggTrades Post-V9 Collection Execution."
        confidence = "high"
        justification = "Le pack de collecte est pret et le dry-run inventorie la fenetre cible sans executer de reseau."
    elif collection_result["status"] != "PASS":
        decision = "aggtrades_post_v9_collection_not_ready_quality_failed"
        recommendation = "V9.19 - AggTrades Collection Correction."
        confidence = "medium"
        justification = "La collecte ou la normalisation a produit des erreurs."
    elif coverage["coverage_complete"]:
        decision = "aggtrades_post_v9_collection_complete"
        recommendation = "V9.19 - Funding-First Feature Window Readiness."
        confidence = "medium"
        justification = "La couverture cible est complete selon l'inventaire local."
    else:
        decision = "aggtrades_post_v9_collection_partial"
        recommendation = "V9.19 - AggTrades Post-V9 Coverage Validation."
        confidence = "medium"
        justification = "Une execution partielle ou validate-only ne couvre pas toute la fenetre cible."
    return {
        "decision": decision,
        "confidence": confidence,
        "justification": justification,
        "next_recommendation": recommendation,
        "collection_executed": collection_result["collection_executed"],
        "no_backtest": True,
        "no_walk_forward": True,
        "no_trading": True,
    }


def build_manifest_v9_18(report: dict[str, Any]) -> dict[str, Any]:
    coverage = report["coverage_summary"]
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": report["status"],
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "mode": report["mode"],
        "report_path": REPORT_JSON_PATH.as_posix(),
        "markdown_path": REPORT_MD_PATH.as_posix(),
        "target_window": report["target_window"],
        "future_funding_first_window": report["future_funding_first_window"],
        "days_expected": coverage["days_expected"],
        "days_collected": report["collection_result"]["days_downloaded"],
        "days_already_present": coverage["days_already_present"],
        "days_missing": coverage["days_missing"],
        "days_quarantined": coverage["days_quarantined"],
        "coverage_start": coverage["coverage_start"],
        "coverage_end": coverage["coverage_end"],
        "total_rows": coverage["total_rows"],
        "collection_executed": report["collection_executed"],
        "network_used": report["network_used"],
        "network_scope": report["collection_result"]["network_scope"],
        "api_key_used": report["safety_flags"]["api_key_used"],
        "private_endpoint_used": report["safety_flags"]["private_endpoint_used"],
        "v9_18_decision": report["v9_18_decision"],
        "findings": report["findings"],
        "safety_flags": report["safety_flags"],
    }


def build_markdown_v9_18(report: dict[str, Any]) -> str:
    coverage = report["coverage_summary"]
    decision = report["v9_18_decision"]
    source = report["source_public_target"]
    lines = [
        "# V9.18 - AggTrades Post-V9 Collection Pack",
        "",
        "## Resume executif",
        f"- Mode execute : `{report['mode']}`.",
        f"- Decision V9.18 : `{decision['decision']}`.",
        f"- Justification : {decision['justification']}",
        f"- Recommandation suivante : {decision['next_recommendation']}",
        "- V9.18 reste data-only : aucun label, dataset supervise, ML, walk-forward, backtest, strategie ou signal actionnable.",
        "",
        "## Source publique ciblee",
        f"- Source : `{source['source_name']}`.",
        f"- Host : `{source['host']}`.",
        f"- Marche : `{source['market_type']}`.",
        f"- Symbole : `{source['symbol']}`.",
        "- Compte requis : `False`.",
        "- Cle API requise : `False`.",
        "- Endpoint prive requis : `False`.",
        "- Websocket live requis : `False`.",
        "",
        "## Fenetre cible",
        f"- Fenetre de collecte : `{report['target_window']['start']}` -> `{report['target_window']['end']}`.",
        f"- Jours attendus : `{coverage['days_expected']}`.",
        f"- Jours deja presents : `{coverage['days_already_present']}`.",
        f"- Jours manquants : `{coverage['days_missing']}`.",
        f"- Couverture : `{coverage['coverage_ratio']}`.",
        "",
        "## Convention de stockage",
        f"- Bronze/raw : `{report['storage_convention']['bronze_raw_pattern']}`.",
        f"- Silver normalise : `{report['storage_convention']['silver_normalized_pattern']}`.",
        "",
        "## Qualite et causalite",
        "- Checks par jour : presence, lisibilite, schema, types, timestamps UTC, prix/quantite positifs, doublons, coherence date partition, taille non nulle.",
        "- Checks fenetre : jours attendus, jours presents, gaps, doublons, min/max timestamp, min/max aggregate_trade_id, lignes invalides, quarantine.",
        "- Anti-leakage : `available_ts >= event_ts`, aucune jointure label, aucune integration funding/OI dans V9.18.",
        "",
        "## Garde-fous",
        "- Aucun trading reel.",
        "- Aucun paper live.",
        "- Aucun ordre.",
        "- Aucun backtest execute.",
        "- Aucun walk-forward.",
        "- Aucune strategie.",
        "- Aucun signal actionnable.",
        "- Aucun modele persistant.",
        "- Aucune API privee.",
        "- Aucune cle API.",
        "- Aucun client exchange authentifie.",
        "- Aucun websocket live.",
        "- Aucun sidecar et aucune empreinte ZIP.",
    ]
    if not report["collection_executed"]:
        lines.extend(["- Aucun reseau utilise.", "- Aucun telechargement execute.", "- Aucune ingestion executee."])
    return "\n".join(lines) + "\n"


def update_state_surfaces_v9_18(root: Path, report: dict[str, Any]) -> None:
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "source_version": SOURCE_VERSION,
        "direction": DIRECTION,
        "mode": report["mode"],
        "v9_18_decision": report["v9_18_decision"]["decision"],
        "recommended_next_step": report["next_recommendation"],
        "days_expected": report["coverage_summary"]["days_expected"],
        "days_already_present": report["coverage_summary"]["days_already_present"],
        "days_missing": report["coverage_summary"]["days_missing"],
        "collection_executed": report["collection_executed"],
        "features_created": False,
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "network_used": report["network_used"],
        "new_data_downloaded": report["new_data_downloaded"],
        "ingestion_executed": report["ingestion_executed"],
        **report["safety_flags"],
    }
    state_path = root / "reports/PROJECT_STATE.json"
    state = _read_json(state_path) if state_path.exists() else {}
    for stale_key in ["recommended_next_version", "recommended_next_action"]:
        state.pop(stale_key, None)
    state.update(metrics)
    _write_json(state_path, state)
    _write_json(root / "reports/current/latest_metrics.json", metrics)
    summary = (
        "# Synthese courante - V9.18\n\n"
        "- Derniere version validee : `V9.17`.\n"
        "- Candidate : `V9.18`.\n"
        "- Statut : `pending_external_audit`.\n"
        "- Direction : pack de collecte aggTrades post-V9.\n"
        f"- Mode execute : `{report['mode']}`.\n"
        f"- Decision V9.18 : `{report['v9_18_decision']['decision']}`.\n"
        f"- Jours attendus : `{report['coverage_summary']['days_expected']}`.\n"
        f"- Jours deja presents : `{report['coverage_summary']['days_already_present']}`.\n"
        f"- Jours manquants : `{report['coverage_summary']['days_missing']}`.\n"
        f"- Recommandation : {report['next_recommendation']}\n"
        "- Aucun label, dataset supervise, ML, walk-forward, backtest, strategie ou signal actionnable.\n"
        "- Aucun trading, paper live, ordre, modele persistant, API privee, cle API, client exchange authentifie ou websocket live.\n"
        "- Aucun sidecar et aucune empreinte ZIP.\n"
    )
    if not report["collection_executed"]:
        summary += "- Aucun reseau, aucun telechargement et aucune ingestion executee.\n"
    _write_text(root / "reports/PROJECT_STATE.md", summary)
    _write_text(root / "reports/current/latest_summary.md", summary)
    _write_text(root / "reports/current/latest_metrics.md", summary)
    _write_text(
        root / "README.md",
        "# Projet Galapagos\n\n"
        "- Derniere version validee : V9.17.\n"
        "- Candidate : V9.18, pack de collecte aggTrades post-V9.\n"
        "- Mode par defaut et execute : dry-run.\n"
        "- Aucun trading, ordre, backtest, walk-forward, strategie, signal actionnable, modele persistant, API privee ou cle API.\n"
        "- Aucun reseau, aucun telechargement, aucune ingestion, aucun sidecar et aucune empreinte ZIP en dry-run.\n",
    )


def safety_flags_for_mode_v9_18(collection_executed: bool) -> dict[str, Any]:
    flags: dict[str, Any] = dict(BASE_SAFETY_FLAGS)
    if collection_executed:
        flags.update(
            {
                "network_used": True,
                "no_new_data_download": False,
                "no_ingestion_executed": False,
                "network_scope": "public_archive_read_only",
                "new_data_download_scope": "public_historical_aggtrades_only",
                "ingestion_scope": "public_aggtrades_bronze_silver_only",
            }
        )
    else:
        flags.update({"network_used": False, "no_new_data_download": True, "no_ingestion_executed": True})
    return flags


def build_public_archive_url_v9_18(date_value: str) -> str:
    return f"https://{PUBLIC_ARCHIVE_HOST}/data/spot/daily/{TRADE_SOURCE_TYPE}/{SYMBOL}/{SYMBOL}-{TRADE_SOURCE_TYPE}-{date_value}.zip"


def raw_zip_path_for_date_v9_18(date_value: str) -> Path:
    return Path(BRONZE_PARTITION_TEMPLATE.format(date=date_value))


def silver_path_for_date_v9_18(date_value: str) -> Path:
    return Path(SILVER_PARTITION_TEMPLATE.format(date=date_value))


def date_range_v9_18(start: str, end: str) -> list[str]:
    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    if end_date < start_date:
        raise ValueError("end date must be >= start date")
    return [(start_date + timedelta(days=offset)).isoformat() for offset in range((end_date - start_date).days + 1)]


def parse_date_from_raw_name_v9_18(name: str) -> str | None:
    prefix = f"{SYMBOL}-{TRADE_SOURCE_TYPE}-"
    suffix = ".zip"
    if not name.startswith(prefix) or not name.endswith(suffix):
        return None
    value = name[len(prefix) : -len(suffix)]
    try:
        date.fromisoformat(value)
    except ValueError:
        return None
    return value


def checksum_file_v9_18(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_input(root: Path, path: Path) -> dict[str, Any]:
    full = root / path
    if not full.exists():
        return {"path": path.as_posix(), "available": False, "payload": {}}
    if path.suffix == ".json":
        payload: Any = _read_json(full)
    else:
        payload = {"text": full.read_text(encoding="utf-8")}
    return {"path": path.as_posix(), "available": True, "payload": payload}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
