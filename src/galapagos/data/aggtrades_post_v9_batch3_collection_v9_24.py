from __future__ import annotations

import json
import time
import zipfile
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from galapagos.data.aggtrades_post_v9_collection_v9_18 import (
    ALLOWED_PUBLIC_HOSTS,
    BASE_SAFETY_FLAGS as BASE_SAFETY_FLAGS_V9_18,
    BRONZE_PARTITION_TEMPLATE,
    FINDINGS,
    FUNDING_FIRST_END,
    FUNDING_FIRST_START,
    INPUT_PATHS as INPUT_PATHS_V9_18,
    MARKET_TYPE,
    PUBLIC_ARCHIVE_HOST,
    QUALITY_CHECKS,
    QUARANTINE_DIR,
    RAW_DIR,
    SILVER_COLUMNS_V9_18,
    SILVER_PARTITION_TEMPLATE,
    SOURCE_STORAGE,
    SYMBOL,
    TARGET_END,
    TARGET_START,
    TRADE_SOURCE_TYPE,
    VENUE,
    build_public_archive_url_v9_18,
    checksum_file_v9_18,
    normalize_raw_zip_to_silver_v9_18,
    parse_date_from_raw_name_v9_18,
    raw_zip_path_for_date_v9_18,
    silver_path_for_date_v9_18,
)


VERSION = "V9.24"
LAST_VALIDATED_VERSION = "V9.23"
SOURCE_VERSION = "V9.23"
DIRECTION = "aggtrades_post_v9_batch3_collection"
BATCH_ID = "V9.24_batch_03"

BATCH_START = "2024-10-09"
BATCH_END = "2024-12-07"
MAX_BATCH_DOWNLOADS = 60
PREVIOUS_COVERAGE_START = "2024-05-05"
PREVIOUS_COVERAGE_END = "2024-10-08"

REPORT_JSON_PATH = Path("reports/data/aggtrades_post_v9_batch3_collection_v9_24.json")
REPORT_MD_PATH = Path("reports/data/aggtrades_post_v9_batch3_collection_v9_24.md")
MANIFEST_PATH = Path("reports/manifests/aggtrades_post_v9_batch3_collection_v9_24_manifest.json")
DOC_PATH = Path("docs/aggtrades_post_v9_batch3_collection_v9_24.md")

ALLOWED_MODES = {"dry-run", "collect", "validate-only"}
ALLOWED_DECISIONS = {
    "aggtrades_post_v9_batch3_collection_success",
    "aggtrades_post_v9_batch3_collection_partial",
    "aggtrades_post_v9_batch3_collection_failed_source_issue",
    "aggtrades_post_v9_batch3_collection_failed_quality",
    "aggtrades_post_v9_batch3_collection_not_executed",
    "stop_aggtrades_collection_branch",
}

INPUT_PATHS = {
    "v9_23_batch2_collection": Path("reports/data/aggtrades_post_v9_batch2_collection_v9_23.json"),
    "v9_23_manifest": Path("reports/manifests/aggtrades_post_v9_batch2_collection_v9_23_manifest.json"),
    "v9_22_multi_batch_plan": Path("reports/data/aggtrades_post_v9_multi_batch_plan_v9_22.json"),
    "v9_22_manifest": Path("reports/manifests/aggtrades_post_v9_multi_batch_plan_v9_22_manifest.json"),
    "v9_21_batch_expansion": Path("reports/data/aggtrades_post_v9_batch_expansion_v9_21.json"),
    "v9_21_manifest": Path("reports/manifests/aggtrades_post_v9_batch_expansion_v9_21_manifest.json"),
    "v9_20_batch_collection": Path("reports/data/aggtrades_post_v9_batch_collection_v9_20.json"),
    "v9_20_manifest": Path("reports/manifests/aggtrades_post_v9_batch_collection_v9_20_manifest.json"),
    "v9_19_pilot_collection": Path("reports/data/aggtrades_post_v9_pilot_collection_v9_19.json"),
    "v9_19_manifest": Path("reports/manifests/aggtrades_post_v9_pilot_collection_v9_19_manifest.json"),
    "v9_18_collection_pack": Path("reports/data/aggtrades_post_v9_collection_v9_18.json"),
    "v9_18_manifest": Path("reports/manifests/aggtrades_post_v9_collection_v9_18_manifest.json"),
    "v9_17_collection_plan": Path("reports/research_decisions/derivatives_history_collection_plan_v9_17.json"),
    "v9_16_window_diagnostic": Path("reports/research_decisions/derivatives_window_extension_v9_16.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
    "latest_summary": Path("reports/current/latest_summary.md"),
    "project_state": Path("reports/PROJECT_STATE.json"),
    "project_state_md": Path("reports/PROJECT_STATE.md"),
}

BASE_SAFETY_FLAGS = {
    **BASE_SAFETY_FLAGS_V9_18,
    "network_used": False,
    "new_data_downloaded": False,
    "ingestion_executed": False,
    "no_new_data_download": True,
    "no_ingestion_executed": True,
}


def run_aggtrades_post_v9_batch3_collection_v9_24(
    root: Path = Path("."),
    *,
    mode: str = "dry-run",
    start_date: str = BATCH_START,
    end_date: str = BATCH_END,
    max_downloads: int | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    report = build_aggtrades_post_v9_batch_report_v9_24(
        root,
        mode=mode,
        start_date=start_date,
        end_date=end_date,
        max_downloads=max_downloads,
    )
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_24(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / MANIFEST_PATH, build_manifest_v9_24(report))
    update_state_surfaces_v9_24(root, report)
    return report


def build_aggtrades_post_v9_batch_report_v9_24(
    root: Path = Path("."),
    *,
    mode: str = "dry-run",
    start_date: str = BATCH_START,
    end_date: str = BATCH_END,
    max_downloads: int | None = None,
) -> dict[str, Any]:
    if mode not in ALLOWED_MODES:
        raise ValueError(f"unsupported V9.24 mode: {mode}")
    requested_dates = date_range_v9_24(start_date, end_date)
    validate_batch_request_v9_24(mode, requested_dates, max_downloads)
    root = root.resolve()
    started = time.monotonic()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    previous_coverage_check = build_previous_coverage_check_v9_24(root)
    day_plan_before = build_batch_day_plan_v9_24(root, requested_dates)
    collection_result = execute_batch_mode_v9_24(
        root,
        mode,
        requested_dates,
        max_downloads=max_downloads,
    )
    day_plan_after = build_batch_day_plan_v9_24(root, requested_dates)
    day_validation = [validate_batch_day_v9_24(root, day_value) for day_value in requested_dates]
    runtime_seconds = round(time.monotonic() - started, 3)
    batch_summary = summarize_batch_validation_v9_24(
        requested_dates,
        day_plan_before,
        collection_result,
        day_validation,
        runtime_seconds,
        previous_coverage_check,
    )
    reported_cumulative_coverage = build_reported_cumulative_coverage_v9_24(inputs, batch_summary)
    local_file_coverage = build_local_file_coverage_v9_24(root, FUNDING_FIRST_START, BATCH_END)
    batch_summary.update(
        {
            "reported_cumulative_coverage_start": reported_cumulative_coverage["reported_cumulative_coverage_start"],
            "reported_cumulative_coverage_end": reported_cumulative_coverage["reported_cumulative_coverage_end"],
            "local_file_coverage_start": local_file_coverage["local_file_coverage_start"],
            "local_file_coverage_end": local_file_coverage["local_file_coverage_end"],
        }
    )
    safety_flags = safety_flags_for_batch_v9_24(collection_result)
    decision = decide_v9_24(collection_result, batch_summary)
    status = "PASS" if collection_result["status"] == "PASS" and not batch_summary["quality_errors"] else "FAIL"
    if mode != "collect" and decision["decision"] == "aggtrades_post_v9_batch3_collection_not_executed":
        status = "PASS"
    report = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": status,
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "mode": mode,
        "inputs_used": {name: {"path": item["path"], "available": item["available"]} for name, item in inputs.items()},
        "source_public_target": build_source_design_v9_24(),
        "global_target_window": {
            "start": TARGET_START,
            "end": TARGET_END,
            "days_expected": len(date_range_v9_24(TARGET_START, TARGET_END)),
            "complete_collection_reached": False,
        },
        "future_funding_first_window": {
            "start": FUNDING_FIRST_START,
            "end": FUNDING_FIRST_END,
            "days_expected": len(date_range_v9_24(FUNDING_FIRST_START, FUNDING_FIRST_END)),
            "complete_collection_reached": False,
        },
        "batch_window": {
            "batch_id": BATCH_ID,
            "start": start_date,
            "end": end_date,
            "max_downloads": max_downloads,
            "days_requested": len(requested_dates),
            "requested_dates": requested_dates,
        },
        "previous_coverage_check": previous_coverage_check,
        "reported_cumulative_coverage": reported_cumulative_coverage,
        "local_file_coverage": local_file_coverage,
        "audit_lite_mode_handling": {
            "repo_local_full_data_mode": "V9.24 runner inspects local raw/silver files and writes a full local report only in the local repository.",
            "audit_lite_without_full_data_mode": "Audit-lite smoke validates the delivered report and manifests; it does not rerun collection and does not rewrite coverage from missing full data.",
            "avoid_contradictory_regeneration_without_full_data": True,
        },
        "storage_convention": {
            "raw_pattern": BRONZE_PARTITION_TEMPLATE,
            "silver_pattern": SILVER_PARTITION_TEMPLATE,
            "quarantine_dir": QUARANTINE_DIR.as_posix(),
            "raw_dir": RAW_DIR.as_posix(),
        },
        "day_plan_before": day_plan_before,
        "day_plan_after": day_plan_after,
        "collection_result": collection_result,
        "batch_validation": {
            "day_results": day_validation,
            "summary": batch_summary,
        },
        "quality_checks": list(QUALITY_CHECKS),
        "silver_schema_columns": list(SILVER_COLUMNS_V9_18),
        "anti_leakage_plan": build_anti_leakage_plan_v9_24(),
        "v9_24_decision": decision,
        "next_recommendation": decision["next_recommendation"],
        "collection_executed": collection_result["collection_executed"],
        "network_used": collection_result["network_used"],
        "new_data_downloaded": collection_result["new_data_downloaded"],
        "ingestion_executed": collection_result["ingestion_executed"],
        "complete_collection_reached": False,
        "features_created": False,
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "blockers": collection_result["errors"],
        "warnings": build_warnings_v9_24(collection_result, batch_summary),
        "limitations": [
            "V9.24 ne collecte pas la fenetre complete de 772 jours.",
            "Le batch valide le pipeline public archive -> raw ZIP -> silver Parquet sur un echantillon borne.",
            "La couverture cumulee declaree vient des rapports valides; la couverture locale reelle vient de l'inventaire raw/silver local.",
            "Aucune integration funding/open-interest, aucun label, aucun dataset supervise, aucun ML et aucun walk-forward ne sont executes.",
        ],
        "findings": dict(FINDINGS),
        "safety_flags": safety_flags,
    }
    return report


def validate_batch_request_v9_24(mode: str, requested_dates: list[str], max_downloads: int | None) -> None:
    if not requested_dates:
        raise ValueError("V9.24 batch window cannot be empty.")
    if len(requested_dates) > MAX_BATCH_DOWNLOADS:
        raise ValueError("V9.24 batch window is limited to 60 days.")
    if mode == "collect":
        if max_downloads is None:
            raise ValueError("V9.24 collect mode requires --max-downloads to prevent accidental bulk collection.")
        if max_downloads <= 0 or max_downloads > MAX_BATCH_DOWNLOADS:
            raise ValueError("V9.24 collect mode requires 1 <= --max-downloads <= 60.")
        if max_downloads > len(requested_dates):
            raise ValueError("V9.24 --max-downloads cannot exceed requested batch days.")


def build_source_design_v9_24() -> dict[str, Any]:
    return {
        "source_name": "Binance public archive aggTrades daily files",
        "host": PUBLIC_ARCHIVE_HOST,
        "allowed_public_hosts": sorted(ALLOWED_PUBLIC_HOSTS),
        "venue": VENUE,
        "market_type": MARKET_TYPE,
        "symbol": SYMBOL,
        "trade_source_type": TRADE_SOURCE_TYPE,
        "batch_window": f"{BATCH_START}_{BATCH_END}",
        "global_target_window": f"{TARGET_START}_{TARGET_END}",
        "funding_first_research_window": f"{FUNDING_FIRST_START}_{FUNDING_FIRST_END}",
        "account_required": False,
        "api_key_required": False,
        "private_endpoint_required": False,
        "exchange_auth_required": False,
        "websocket_live_required": False,
        "download_url_template": f"https://{PUBLIC_ARCHIVE_HOST}/data/spot/daily/aggTrades/BTCUSDT/BTCUSDT-aggTrades-YYYY-MM-DD.zip",
        "expected_silver_columns": list(SILVER_COLUMNS_V9_18),
    }


def build_batch_day_plan_v9_24(root: Path, requested_dates: list[str]) -> list[dict[str, Any]]:
    plan: list[dict[str, Any]] = []
    for day_value in requested_dates:
        raw_path = root / raw_zip_path_for_date_v9_18(day_value)
        silver_path = root / silver_path_for_date_v9_18(day_value)
        status = "day_missing"
        if raw_path.exists() and raw_path.stat().st_size <= 0:
            status = "day_partial"
        elif raw_path.exists() and silver_path.exists():
            status = "day_complete"
        elif raw_path.exists():
            status = "day_raw_present"
        elif silver_path.exists():
            status = "day_silver_without_raw"
        plan.append(
            {
                "date": day_value,
                "status": status,
                "raw_path": raw_zip_path_for_date_v9_18(day_value).as_posix(),
                "silver_path": silver_path_for_date_v9_18(day_value).as_posix(),
                "public_url": build_public_archive_url_v9_18(day_value),
                "raw_exists": raw_path.exists(),
                "raw_bytes": raw_path.stat().st_size if raw_path.exists() else 0,
                "silver_exists": silver_path.exists(),
                "silver_bytes": silver_path.stat().st_size if silver_path.exists() else 0,
            }
        )
    return plan


def build_previous_coverage_check_v9_24(root: Path) -> dict[str, Any]:
    previous_dates = date_range_v9_24(PREVIOUS_COVERAGE_START, PREVIOUS_COVERAGE_END)
    day_plan = build_batch_day_plan_v9_24(root, previous_dates)
    complete_dates = [item["date"] for item in day_plan if item["status"] == "day_complete"]
    missing_dates = [item["date"] for item in day_plan if item["status"] != "day_complete"]
    v9_19_report_path = root / "reports/data/aggtrades_post_v9_pilot_collection_v9_19.json"
    v9_20_report_path = root / "reports/data/aggtrades_post_v9_batch_collection_v9_20.json"
    v9_21_report_path = root / "reports/data/aggtrades_post_v9_batch_expansion_v9_21.json"
    v9_22_report_path = root / "reports/data/aggtrades_post_v9_multi_batch_plan_v9_22.json"
    v9_23_report_path = root / "reports/data/aggtrades_post_v9_batch2_collection_v9_23.json"
    previous_complete = len(complete_dates) == len(previous_dates)
    return {
        "previous_coverage_start": PREVIOUS_COVERAGE_START,
        "previous_coverage_end": PREVIOUS_COVERAGE_END,
        "days_expected": len(previous_dates),
        "days_complete": len(complete_dates),
        "complete_dates": complete_dates,
        "missing_or_incomplete_dates": missing_dates,
        "v9_19_report_available": v9_19_report_path.is_file(),
        "v9_20_report_available": v9_20_report_path.is_file(),
        "v9_21_report_available": v9_21_report_path.is_file(),
        "v9_22_report_available": v9_22_report_path.is_file(),
        "v9_23_report_available": v9_23_report_path.is_file(),
        "local_previous_days_present_and_complete": previous_complete,
        "v9_24_can_run_independently": True,
        "reported_cumulative_coverage_allowed": v9_23_report_path.is_file() or v9_22_report_path.is_file(),
        "local_cumulative_coverage_claim_allowed": previous_complete,
        "note": "V9.24 peut s'executer independamment; la couverture cumulee declaree vient des rapports valides, tandis que la couverture locale reelle exige les fichiers raw/silver.",
    }


def execute_batch_mode_v9_24(
    root: Path,
    mode: str,
    requested_dates: list[str],
    *,
    max_downloads: int | None,
) -> dict[str, Any]:
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
            "days_skipped_existing": 0,
            "errors": [],
            "downloaded_dates": [],
            "normalized_dates": [],
            "skipped_existing_dates": [],
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
            "days_attempted": len(requested_dates),
            "days_downloaded": 0,
            "days_normalized": 0,
            "days_skipped_existing": 0,
            "errors": [],
            "downloaded_dates": [],
            "normalized_dates": [],
            "skipped_existing_dates": [],
        }
    return collect_batch_public_aggtrades_v9_24(root, requested_dates, max_downloads=max_downloads)


def collect_batch_public_aggtrades_v9_24(
    root: Path,
    requested_dates: list[str],
    *,
    max_downloads: int | None,
) -> dict[str, Any]:
    validate_batch_request_v9_24("collect", requested_dates, max_downloads)
    attempted_dates: list[str] = []
    skipped_existing_dates: list[str] = []
    errors: list[str] = []
    downloaded_dates: list[str] = []
    normalized_dates: list[str] = []
    for day_value in requested_dates:
        raw_path = root / raw_zip_path_for_date_v9_18(day_value)
        silver_path = root / silver_path_for_date_v9_18(day_value)
        if raw_path.exists() and raw_path.stat().st_size > 0 and silver_path.exists() and silver_path.stat().st_size > 0:
            skipped_existing_dates.append(day_value)
            continue
        if len(attempted_dates) >= (max_downloads or 0):
            break
        attempted_dates.append(day_value)
        try:
            before_exists = raw_path.exists() and raw_path.stat().st_size > 0
            download_public_archive_v9_24(build_public_archive_url_v9_18(day_value), raw_path)
            after_exists = raw_path.exists() and raw_path.stat().st_size > 0
            if after_exists and not before_exists:
                downloaded_dates.append(day_value)
            normalize_raw_zip_to_silver_v9_18(raw_path, silver_path, day_value)
            normalized_dates.append(day_value)
        except Exception as exc:  # noqa: BLE001 - the batch must report each daily failure precisely.
            quarantine_path = quarantine_failed_raw_v9_24(root, day_value, raw_path)
            suffix = f"; quarantined={quarantine_path.as_posix()}" if quarantine_path else ""
            errors.append(f"{day_value}: {exc}{suffix}")
    return {
        "mode": "collect",
        "status": "PASS" if not errors else "FAIL",
        "collection_executed": True,
        "network_used": bool(attempted_dates),
        "new_data_downloaded": bool(downloaded_dates),
        "ingestion_executed": bool(normalized_dates),
        "network_scope": "public_archive_read_only",
        "new_data_download_scope": "public_historical_aggtrades_batch3_only",
        "ingestion_scope": "public_aggtrades_bronze_silver_batch3_only",
        "days_attempted": len(attempted_dates),
        "days_downloaded": len(downloaded_dates),
        "days_normalized": len(normalized_dates),
        "days_skipped_existing": len(skipped_existing_dates),
        "errors": errors,
        "downloaded_dates": downloaded_dates,
        "normalized_dates": normalized_dates,
        "skipped_existing_dates": skipped_existing_dates,
    }


def download_public_archive_v9_24(url: str, destination: Path) -> None:
    from urllib.parse import urlparse
    from urllib.request import Request, urlopen

    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc not in ALLOWED_PUBLIC_HOSTS:
        raise ValueError("V9.24 allows public read-only downloads from data.binance.vision only.")
    if destination.exists() and destination.stat().st_size > 0:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = destination.with_suffix(destination.suffix + ".part")
    if tmp_path.exists():
        tmp_path.unlink()
    request = Request(url, headers={"User-Agent": "galapagos-v9.24-public-read-only"})
    with urlopen(request, timeout=180) as response:
        if getattr(response, "status", 200) != 200:
            raise RuntimeError(f"public archive download failed with status {response.status}")
        with tmp_path.open("wb") as handle:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
    if tmp_path.stat().st_size <= 0:
        tmp_path.unlink(missing_ok=True)
        raise RuntimeError("downloaded public archive is empty")
    if not zipfile.is_zipfile(tmp_path):
        quarantine = destination.parent / f"{destination.name}.invalid"
        tmp_path.replace(quarantine)
        raise RuntimeError(f"downloaded public archive is not a ZIP; quarantined={quarantine.as_posix()}")
    tmp_path.replace(destination)


def validate_batch_day_v9_24(root: Path, day_value: str) -> dict[str, Any]:
    raw_path = root / raw_zip_path_for_date_v9_18(day_value)
    silver_path = root / silver_path_for_date_v9_18(day_value)
    errors: list[str] = []
    raw_bytes = raw_path.stat().st_size if raw_path.exists() else 0
    silver_bytes = silver_path.stat().st_size if silver_path.exists() else 0
    if not raw_path.exists():
        errors.append("raw_zip_missing")
    elif raw_bytes <= 0:
        errors.append("raw_zip_empty")
    elif not zipfile.is_zipfile(raw_path):
        errors.append("raw_zip_unreadable")
    else:
        try:
            with zipfile.ZipFile(raw_path) as archive:
                csv_names = [name for name in archive.namelist() if name.endswith(".csv")]
                if len(csv_names) != 1:
                    errors.append("raw_zip_expected_single_csv")
        except zipfile.BadZipFile:
            errors.append("raw_zip_bad_zip")
    if not silver_path.exists():
        errors.append("silver_parquet_missing")
        return _day_result(day_value, raw_path, silver_path, raw_bytes, silver_bytes, errors)
    try:
        import pandas as pd

        frame = pd.read_parquet(silver_path)
        missing_columns = [column for column in SILVER_COLUMNS_V9_18 if column not in frame.columns]
        if missing_columns:
            errors.append(f"silver_missing_columns={missing_columns}")
            return _day_result(day_value, raw_path, silver_path, raw_bytes, silver_bytes, errors)
        rows = len(frame)
        duplicates = int(frame["aggregate_trade_id"].duplicated().sum())
        invalid_rows = int((frame["row_valid"] != True).sum())  # noqa: E712 - pandas boolean comparison.
        event_ts = pd.to_datetime(frame["event_ts"], utc=True)
        available_ts = pd.to_datetime(frame["available_ts"], utc=True)
        partition_mismatch = int((event_ts.dt.date.astype(str) != day_value).sum())
        non_positive_price = int((frame["price"].astype(float) <= 0).sum())
        non_positive_quantity = int((frame["quantity"].astype(float) <= 0).sum())
        availability_violations = int((available_ts < event_ts).sum())
        monotone = bool(frame["aggregate_trade_id"].is_monotonic_increasing)
        if rows == 0:
            errors.append("silver_zero_rows")
        if duplicates:
            errors.append(f"duplicate_aggregate_trade_id={duplicates}")
        if partition_mismatch:
            errors.append(f"partition_event_ts_mismatch={partition_mismatch}")
        if non_positive_price:
            errors.append(f"price_non_positive={non_positive_price}")
        if non_positive_quantity:
            errors.append(f"quantity_non_positive={non_positive_quantity}")
        if availability_violations:
            errors.append(f"available_ts_before_event_ts={availability_violations}")
        if not monotone:
            errors.append("aggregate_trade_id_not_monotone")
        result = _day_result(day_value, raw_path, silver_path, raw_bytes, silver_bytes, errors)
        result.update(
            {
                "rows": rows,
                "invalid_rows": invalid_rows,
                "duplicates": duplicates,
                "min_event_ts": event_ts.min().isoformat().replace("+00:00", "Z") if rows else None,
                "max_event_ts": event_ts.max().isoformat().replace("+00:00", "Z") if rows else None,
                "min_aggregate_trade_id": int(frame["aggregate_trade_id"].min()) if rows else None,
                "max_aggregate_trade_id": int(frame["aggregate_trade_id"].max()) if rows else None,
                "source_checksum": checksum_file_v9_18(raw_path) if raw_path.exists() and raw_bytes > 0 else None,
            }
        )
        return result
    except Exception as exc:  # noqa: BLE001 - validator reports dependency or parquet failures explicitly.
        errors.append(f"silver_read_failed={exc}")
        return _day_result(day_value, raw_path, silver_path, raw_bytes, silver_bytes, errors)


def _day_result(
    day_value: str,
    raw_path: Path,
    silver_path: Path,
    raw_bytes: int,
    silver_bytes: int,
    errors: list[str],
) -> dict[str, Any]:
    status = "day_complete" if not errors else "day_failed"
    return {
        "date": day_value,
        "status": status,
        "raw_path": raw_path.as_posix(),
        "silver_path": silver_path.as_posix(),
        "raw_bytes": raw_bytes,
        "silver_bytes": silver_bytes,
        "rows": 0,
        "invalid_rows": None,
        "duplicates": None,
        "min_event_ts": None,
        "max_event_ts": None,
        "min_aggregate_trade_id": None,
        "max_aggregate_trade_id": None,
        "errors": errors,
    }


def summarize_batch_validation_v9_24(
    requested_dates: list[str],
    day_plan_before: list[dict[str, Any]],
    collection_result: dict[str, Any],
    day_validation: list[dict[str, Any]],
    runtime_seconds: float,
    previous_coverage_check: dict[str, Any],
) -> dict[str, Any]:
    complete_days = [item for item in day_validation if item["status"] == "day_complete"]
    failed_days = [item for item in day_validation if item["status"] == "day_failed"]
    raw_bytes_total = sum(int(item.get("raw_bytes") or 0) for item in day_validation)
    silver_bytes_total = sum(int(item.get("silver_bytes") or 0) for item in day_validation)
    total_rows = sum(int(item.get("rows") or 0) for item in day_validation)
    invalid_rows = sum(int(item.get("invalid_rows") or 0) for item in day_validation if item.get("invalid_rows") is not None)
    duplicates = sum(int(item.get("duplicates") or 0) for item in day_validation if item.get("duplicates") is not None)
    min_event_values = [item["min_event_ts"] for item in day_validation if item.get("min_event_ts")]
    max_event_values = [item["max_event_ts"] for item in day_validation if item.get("max_event_ts")]
    min_ids = [int(item["min_aggregate_trade_id"]) for item in day_validation if item.get("min_aggregate_trade_id") is not None]
    max_ids = [int(item["max_aggregate_trade_id"]) for item in day_validation if item.get("max_aggregate_trade_id") is not None]
    aggregate_trade_id_gap_warnings = build_aggregate_trade_id_gap_warnings_v9_24(complete_days)
    days_already_complete_before = sum(1 for item in day_plan_before if item["status"] == "day_complete")
    attempted = int(collection_result.get("days_attempted") or 0)
    skipped_existing = int(collection_result.get("days_skipped_existing") or 0)
    average_rows = int(total_rows / len(complete_days)) if complete_days else 0
    average_raw_bytes = int(raw_bytes_total / len(complete_days)) if complete_days else 0
    average_runtime = runtime_seconds / max(attempted, 1)
    target_days = len(date_range_v9_24(TARGET_START, TARGET_END))
    coverage_after_start = complete_days[0]["date"] if complete_days else None
    coverage_after_end = complete_days[-1]["date"] if complete_days else None
    cumulative_start = PREVIOUS_COVERAGE_START if previous_coverage_check["local_previous_days_present_and_complete"] and len(complete_days) == len(requested_dates) else None
    cumulative_end = coverage_after_end if cumulative_start else None
    return {
        "days_requested": len(requested_dates),
        "days_attempted": attempted,
        "days_downloaded": int(collection_result.get("days_downloaded") or 0),
        "days_normalized": int(collection_result.get("days_normalized") or 0),
        "days_skipped_existing": skipped_existing,
        "days_complete": len(complete_days),
        "days_failed": len(failed_days),
        "days_quarantined": sum(1 for item in day_validation if item["status"] == "day_quarantined"),
        "days_already_complete_before": days_already_complete_before,
        "requested_dates": requested_dates,
        "complete_dates": [item["date"] for item in complete_days],
        "failed_dates": [item["date"] for item in failed_days],
        "total_rows": total_rows,
        "invalid_rows": invalid_rows,
        "duplicates": duplicates,
        "min_event_ts": min(min_event_values) if min_event_values else None,
        "max_event_ts": max(max_event_values) if max_event_values else None,
        "min_aggregate_trade_id": min(min_ids) if min_ids else None,
        "max_aggregate_trade_id": max(max_ids) if max_ids else None,
        "aggregate_trade_id_gap_warnings": aggregate_trade_id_gap_warnings,
        "raw_bytes_total": raw_bytes_total,
        "silver_bytes_total": silver_bytes_total,
        "runtime_seconds": runtime_seconds,
        "average_rows_per_day": average_rows,
        "average_raw_bytes_per_day": average_raw_bytes,
        "estimated_full_collection_raw_bytes": average_raw_bytes * target_days if average_raw_bytes else None,
        "estimated_full_collection_rows": average_rows * target_days if average_rows else None,
        "estimated_full_collection_runtime_seconds": round(average_runtime * target_days, 3) if attempted else None,
        "coverage_after_batch_start": coverage_after_start,
        "coverage_after_batch_end": coverage_after_end,
        "cumulative_known_coverage_start": cumulative_start,
        "cumulative_known_coverage_end": cumulative_end,
        "reported_cumulative_coverage_start": None,
        "reported_cumulative_coverage_end": None,
        "local_file_coverage_start": cumulative_start,
        "local_file_coverage_end": cumulative_end,
        "complete_collection_reached": False,
        "restartability_status": "resumable_existing_complete_days_are_skipped_and_missing_days_are_collected_up_to_max_downloads",
        "quality_status": "PASS" if not failed_days and duplicates == 0 and invalid_rows == 0 else "FAIL",
        "coverage_status": "batch_complete_not_full_window" if len(complete_days) == len(requested_dates) else "batch_incomplete",
        "future_full_coverage_complete": False,
        "batch_success": len(complete_days) == len(requested_dates) and not failed_days,
        "quality_errors": [error for item in failed_days for error in item.get("errors", [])],
    }


def decide_v9_24(collection_result: dict[str, Any], batch_summary: dict[str, Any]) -> dict[str, Any]:
    if not collection_result["collection_executed"]:
        decision = "aggtrades_post_v9_batch3_collection_not_executed"
        recommendation = "V9.25 - AggTrades Batch 3 Correction."
        confidence = "high"
        justification = "Aucune collecte batche n'a ete executee."
    elif collection_result["status"] != "PASS":
        decision = "aggtrades_post_v9_batch3_collection_failed_source_issue"
        recommendation = "V9.25 - AggTrades Batch 3 Correction."
        confidence = "medium"
        justification = "La collecte publique ou la normalisation a produit au moins une erreur."
    elif batch_summary["quality_status"] != "PASS":
        decision = "aggtrades_post_v9_batch3_collection_failed_quality"
        recommendation = "V9.25 - AggTrades Batch 3 Correction."
        confidence = "medium"
        justification = "La validation qualite du batch a echoue."
    elif batch_summary["days_complete"] == batch_summary["days_requested"]:
        decision = "aggtrades_post_v9_batch3_collection_success"
        recommendation = "V9.25 - AggTrades Post-V9 Batch 4 Collection."
        confidence = "high"
        justification = "Les jours batches demandes ont ete collectes, normalises et valides sans etendre la collecte complete."
    else:
        decision = "aggtrades_post_v9_batch3_collection_partial"
        recommendation = "V9.25 - AggTrades Batch 3 Correction."
        confidence = "medium"
        justification = "Une partie seulement des jours batches est complete."
    return {
        "decision": decision,
        "confidence": confidence,
        "justification": justification,
        "next_recommendation": recommendation,
        "collection_executed": collection_result["collection_executed"],
        "complete_collection_reached": False,
        "no_backtest": True,
        "no_walk_forward": True,
        "no_trading": True,
    }


def build_reported_cumulative_coverage_v9_24(inputs: dict[str, dict[str, Any]], batch_summary: dict[str, Any]) -> dict[str, Any]:
    payload = inputs.get("v9_23_batch2_collection", {}).get("payload", {})
    coverage = payload.get("reported_cumulative_coverage", {}) if isinstance(payload, dict) else {}
    previous_start = coverage.get("reported_cumulative_coverage_start") or PREVIOUS_COVERAGE_START
    previous_end = coverage.get("reported_cumulative_coverage_end") or PREVIOUS_COVERAGE_END
    batch_complete = batch_summary["days_complete"] == batch_summary["days_requested"] and batch_summary["quality_status"] == "PASS"
    return {
        "source": "reports/data/aggtrades_post_v9_batch2_collection_v9_23.json plus V9.24 batch validation",
        "previous_reported_cumulative_coverage_start": previous_start,
        "previous_reported_cumulative_coverage_end": previous_end,
        "reported_cumulative_coverage_start": previous_start if batch_complete else previous_start,
        "reported_cumulative_coverage_end": batch_summary["coverage_after_batch_end"] if batch_complete else previous_end,
        "batch_contribution_start": batch_summary["coverage_after_batch_start"],
        "batch_contribution_end": batch_summary["coverage_after_batch_end"],
        "batch_complete": batch_complete,
        "declarative_from_validated_reports": True,
    }


def build_aggregate_trade_id_gap_warnings_v9_24(day_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(
        [
            item
            for item in day_results
            if item.get("min_aggregate_trade_id") is not None and item.get("max_aggregate_trade_id") is not None
        ],
        key=lambda item: item["date"],
    )
    warnings: list[dict[str, Any]] = []
    for previous, current in zip(ordered, ordered[1:]):
        expected_next = int(previous["max_aggregate_trade_id"]) + 1
        actual_next = int(current["min_aggregate_trade_id"])
        if actual_next != expected_next:
            warnings.append(
                {
                    "previous_date": previous["date"],
                    "current_date": current["date"],
                    "previous_max_aggregate_trade_id": int(previous["max_aggregate_trade_id"]),
                    "current_min_aggregate_trade_id": actual_next,
                    "expected_next_aggregate_trade_id": expected_next,
                    "gap_size": actual_next - expected_next,
                    "severity": "warning",
                }
            )
    return warnings


def build_local_file_coverage_v9_24(root: Path, start_date: str, end_date: str) -> dict[str, Any]:
    dates = date_range_v9_24(start_date, end_date)
    complete_dates: list[str] = []
    missing_or_incomplete: list[str] = []
    raw_missing: list[str] = []
    silver_missing: list[str] = []
    contiguous_broken = False
    for day_value in dates:
        raw_path = root / raw_zip_path_for_date_v9_18(day_value)
        silver_path = root / silver_path_for_date_v9_18(day_value)
        raw_ok = raw_path.exists() and raw_path.stat().st_size > 0
        silver_ok = silver_path.exists() and silver_path.stat().st_size > 0
        if raw_ok and silver_ok and not contiguous_broken:
            complete_dates.append(day_value)
        if not (raw_ok and silver_ok):
            contiguous_broken = True
            missing_or_incomplete.append(day_value)
            if not raw_ok:
                raw_missing.append(day_value)
            if not silver_ok:
                silver_missing.append(day_value)
    return {
        "source": "local raw/silver filesystem metadata",
        "local_file_coverage_start": complete_dates[0] if complete_dates else None,
        "local_file_coverage_end": complete_dates[-1] if complete_dates else None,
        "days_checked": len(dates),
        "days_contiguous_complete": len(complete_dates),
        "missing_or_incomplete_count": len(missing_or_incomplete),
        "missing_or_incomplete_sample": {"first": missing_or_incomplete[:3], "last": missing_or_incomplete[-3:]},
        "raw_missing_count": len(raw_missing),
        "silver_missing_count": len(silver_missing),
        "full_local_data_available_for_checked_window": len(missing_or_incomplete) == 0,
        "audit_lite_without_full_data_safe": True,
    }


def build_manifest_v9_24(report: dict[str, Any]) -> dict[str, Any]:
    summary = report["batch_validation"]["summary"]
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": report["status"],
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "mode": report["mode"],
        "report_path": REPORT_JSON_PATH.as_posix(),
        "markdown_path": REPORT_MD_PATH.as_posix(),
        "batch_window": report["batch_window"],
        "global_target_window": report["global_target_window"],
        "future_funding_first_window": report["future_funding_first_window"],
        "days_requested": summary["days_requested"],
        "days_attempted": summary["days_attempted"],
        "days_downloaded": summary["days_downloaded"],
        "days_normalized": summary["days_normalized"],
        "days_skipped_existing": summary["days_skipped_existing"],
        "days_complete": summary["days_complete"],
        "days_failed": summary["days_failed"],
        "days_quarantined": summary["days_quarantined"],
        "total_rows": summary["total_rows"],
        "invalid_rows": summary["invalid_rows"],
        "duplicates": summary["duplicates"],
        "min_event_ts": summary["min_event_ts"],
        "max_event_ts": summary["max_event_ts"],
        "min_aggregate_trade_id": summary["min_aggregate_trade_id"],
        "max_aggregate_trade_id": summary["max_aggregate_trade_id"],
        "aggregate_trade_id_gap_warnings": summary["aggregate_trade_id_gap_warnings"],
        "raw_bytes_total": summary["raw_bytes_total"],
        "silver_bytes_total": summary["silver_bytes_total"],
        "coverage_after_batch_start": summary["coverage_after_batch_start"],
        "coverage_after_batch_end": summary["coverage_after_batch_end"],
        "cumulative_known_coverage_start": summary["cumulative_known_coverage_start"],
        "cumulative_known_coverage_end": summary["cumulative_known_coverage_end"],
        "reported_cumulative_coverage_start": summary["reported_cumulative_coverage_start"],
        "reported_cumulative_coverage_end": summary["reported_cumulative_coverage_end"],
        "local_file_coverage_start": summary["local_file_coverage_start"],
        "local_file_coverage_end": summary["local_file_coverage_end"],
        "local_file_coverage": report["local_file_coverage"],
        "complete_collection_reached": False,
        "future_full_coverage_complete": False,
        "collection_executed": report["collection_executed"],
        "network_used": report["network_used"],
        "network_scope": report["collection_result"]["network_scope"],
        "api_key_used": report["safety_flags"]["api_key_used"],
        "private_endpoint_used": report["safety_flags"]["private_endpoint_used"],
        "v9_24_decision": report["v9_24_decision"],
        "findings": report["findings"],
        "safety_flags": report["safety_flags"],
    }


def build_markdown_v9_24(report: dict[str, Any]) -> str:
    summary = report["batch_validation"]["summary"]
    decision = report["v9_24_decision"]
    source = report["source_public_target"]
    lines = [
        "# V9.24 - AggTrades Post-V9 Batch 3 Collection",
        "",
        "## Resume executif",
        f"- Mode execute : `{report['mode']}`.",
        f"- Decision V9.24 : `{decision['decision']}`.",
        f"- Justification : {decision['justification']}",
        f"- Recommandation suivante : {decision['next_recommendation']}",
        "- V9.24 reste data-only : aucun label, dataset supervise, ML, walk-forward, backtest, strategie ou signal actionnable.",
        "- Couverture complete future : `False`.",
        "",
        "## Source publique utilisee",
        f"- Source : `{source['source_name']}`.",
        f"- Host : `{source['host']}`.",
        f"- Marche : `{source['market_type']}`.",
        f"- Symbole : `{source['symbol']}`.",
        "- Compte requis : `False`.",
        "- Cle API requise : `False`.",
        "- Endpoint prive requis : `False`.",
        "- Client exchange authentifie requis : `False`.",
        "- Websocket live requis : `False`.",
        "",
        "## Batch",
        f"- Periode batche : `{report['batch_window']['start']}` -> `{report['batch_window']['end']}`.",
        f"- Jours demandes : `{summary['days_requested']}`.",
        f"- Jours tentes : `{summary['days_attempted']}`.",
        f"- Jours telecharges : `{summary['days_downloaded']}`.",
        f"- Jours normalises : `{summary['days_normalized']}`.",
        f"- Jours deja complets skips : `{summary['days_skipped_existing']}`.",
        f"- Jours valides : `{summary['days_complete']}`.",
        f"- Jours echoues : `{summary['days_failed']}`.",
        f"- Jours quarantine : `{summary['days_quarantined']}`.",
        f"- Lignes totales : `{summary['total_rows']}`.",
        f"- Raw bytes total : `{summary['raw_bytes_total']}`.",
        f"- Silver bytes total : `{summary['silver_bytes_total']}`.",
        f"- Runtime secondes : `{summary['runtime_seconds']}`.",
        f"- Alertes continuite aggregate_trade_id intra-batch : `{len(summary['aggregate_trade_id_gap_warnings'])}`.",
        f"- Couverture batch apres execution : `{summary['coverage_after_batch_start']}` -> `{summary['coverage_after_batch_end']}`.",
        f"- Couverture cumulee declaree : `{summary['reported_cumulative_coverage_start']}` -> `{summary['reported_cumulative_coverage_end']}`.",
        f"- Couverture locale reelle : `{summary['local_file_coverage_start']}` -> `{summary['local_file_coverage_end']}`.",
        "- Mode audit-lite : le ZIP valide le rapport livre et ne regenere pas une couverture contradictoire si les donnees full sont absentes.",
        "",
        "## Estimation collecte complete",
        f"- Fenetre cible future : `{report['global_target_window']['start']}` -> `{report['global_target_window']['end']}`.",
        f"- Jours cible complets : `{report['global_target_window']['days_expected']}`.",
        f"- Raw bytes estimes : `{summary['estimated_full_collection_raw_bytes']}`.",
        f"- Lignes estimees : `{summary['estimated_full_collection_rows']}`.",
        f"- Runtime estime secondes : `{summary['estimated_full_collection_runtime_seconds']}`.",
        "",
        "## Qualite et causalite",
        f"- Statut qualite : `{summary['quality_status']}`.",
        f"- Statut couverture : `{summary['coverage_status']}`.",
        "- Anti-leakage : `available_ts >= event_ts`, aucune jointure label, aucune integration funding/OI dans V9.24.",
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
    if report["network_used"]:
        lines.append("- Reseau limite a `public_archive_read_only` sur `data.binance.vision`.")
    return "\n".join(lines) + "\n"


def update_state_surfaces_v9_24(root: Path, report: dict[str, Any]) -> None:
    summary = report["batch_validation"]["summary"]
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "source_version": SOURCE_VERSION,
        "direction": DIRECTION,
        "mode": report["mode"],
        "v9_24_decision": report["v9_24_decision"]["decision"],
        "recommended_next_step": report["next_recommendation"],
        "batch_start": report["batch_window"]["start"],
        "batch_end": report["batch_window"]["end"],
        "days_requested": summary["days_requested"],
        "days_attempted": summary["days_attempted"],
        "days_downloaded": summary["days_downloaded"],
        "days_normalized": summary["days_normalized"],
        "days_skipped_existing": summary["days_skipped_existing"],
        "days_complete": summary["days_complete"],
        "days_failed": summary["days_failed"],
        "days_quarantined": summary["days_quarantined"],
        "total_rows": summary["total_rows"],
        "raw_bytes_total": summary["raw_bytes_total"],
        "silver_bytes_total": summary["silver_bytes_total"],
        "coverage_after_batch_start": summary["coverage_after_batch_start"],
        "coverage_after_batch_end": summary["coverage_after_batch_end"],
        "cumulative_known_coverage_start": summary["cumulative_known_coverage_start"],
        "cumulative_known_coverage_end": summary["cumulative_known_coverage_end"],
        "reported_cumulative_coverage_start": summary["reported_cumulative_coverage_start"],
        "reported_cumulative_coverage_end": summary["reported_cumulative_coverage_end"],
        "local_file_coverage_start": summary["local_file_coverage_start"],
        "local_file_coverage_end": summary["local_file_coverage_end"],
        "collection_executed": report["collection_executed"],
        "complete_collection_reached": False,
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
    text = (
        "# Synthese courante - V9.24\n\n"
        "- Derniere version validee : `V9.23`.\n"
        "- Candidate : `V9.24`.\n"
        "- Statut : `pending_external_audit`.\n"
        "- Direction : collecte batch 3 aggTrades post-V9.\n"
        f"- Periode batche : `{report['batch_window']['start']}` -> `{report['batch_window']['end']}`.\n"
        f"- Decision V9.24 : `{report['v9_24_decision']['decision']}`.\n"
        f"- Jours demandes/tentes/valides : `{summary['days_requested']}` / `{summary['days_attempted']}` / `{summary['days_complete']}`.\n"
        f"- Jours skips deja complets : `{summary['days_skipped_existing']}`.\n"
        f"- Lignes totales : `{summary['total_rows']}`.\n"
        f"- Couverture cumulee declaree : `{summary['reported_cumulative_coverage_start']}` -> `{summary['reported_cumulative_coverage_end']}`.\n"
        f"- Couverture locale reelle : `{summary['local_file_coverage_start']}` -> `{summary['local_file_coverage_end']}`.\n"
        f"- Recommandation : {report['next_recommendation']}\n"
        "- Couverture complete future : `False`.\n"
        "- Aucun label, dataset supervise, ML, walk-forward, backtest, strategie ou signal actionnable.\n"
        "- Aucun trading, paper live, ordre, modele persistant, API privee, cle API, client exchange authentifie ou websocket live.\n"
        "- Aucun sidecar et aucune empreinte ZIP.\n"
    )
    if report["network_used"]:
        text += "- Reseau utilise uniquement pour archive publique read-only `data.binance.vision`.\n"
    _write_text(root / "reports/PROJECT_STATE.md", text)
    _write_text(root / "reports/current/latest_summary.md", text)
    _write_text(root / "reports/current/latest_metrics.md", text)
    _write_text(
        root / "README.md",
        "# Projet Galapagos\n\n"
        "- Derniere version validee : V9.23.\n"
        "- Candidate : V9.24, collecte batch 3 aggTrades post-V9.\n"
        "- Batch limite : 2024-10-09 -> 2024-12-07, maximum 60 jours.\n"
        "- Aucun trading, ordre, backtest, walk-forward, strategie, signal actionnable, modele persistant, API privee ou cle API.\n"
        "- Aucun client exchange authentifie, aucun websocket live, aucun sidecar et aucune empreinte ZIP.\n",
    )


def safety_flags_for_batch_v9_24(collection_result: dict[str, Any]) -> dict[str, Any]:
    flags: dict[str, Any] = dict(BASE_SAFETY_FLAGS)
    if collection_result["collection_executed"]:
        flags.update(
            {
                "network_used": bool(collection_result["network_used"]),
                "new_data_downloaded": bool(collection_result["new_data_downloaded"]),
                "ingestion_executed": bool(collection_result["ingestion_executed"]),
                "no_new_data_download": not bool(collection_result["new_data_downloaded"]),
                "no_ingestion_executed": not bool(collection_result["ingestion_executed"]),
                "network_scope": "public_archive_read_only",
                "new_data_download_scope": "public_historical_aggtrades_batch3_only",
                "ingestion_scope": "public_aggtrades_bronze_silver_batch3_only",
            }
        )
    return flags


def build_anti_leakage_plan_v9_24() -> dict[str, Any]:
    return {
        "rules": [
            "available_ts >= event_ts for every normalized batch row.",
            "V9.24 collects and normalizes aggTrades only; it creates no labels and no supervised dataset.",
            "Funding and open interest are not joined in V9.24.",
            "No future-derived feature, prediction, signal, order, strategy or backtest artifact is created.",
        ],
        "forbidden_outputs": ["label", "prediction", "model_score", "signal", "trading_signal", "order", "backtest", "position_size", "strategy"],
    }


def build_warnings_v9_24(collection_result: dict[str, Any], batch_summary: dict[str, Any]) -> list[str]:
    warnings = [
        "V9.24 ne couvre pas la fenetre complete de 772 jours.",
        "Les raw/silver batches restent locaux et sont exclus du ZIP audit-lite.",
    ]
    if collection_result["errors"]:
        warnings.append("Des erreurs de collecte ou normalisation sont presentes dans le batch.")
    if batch_summary["days_complete"] < batch_summary["days_requested"]:
        warnings.append("Tous les jours batches demandes ne sont pas valides.")
    return warnings


def quarantine_failed_raw_v9_24(root: Path, day_value: str, raw_path: Path) -> Path | None:
    if not raw_path.exists():
        return None
    quarantine_dir = root / QUARANTINE_DIR / f"date={day_value}"
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    quarantine_path = quarantine_dir / raw_path.name
    raw_path.replace(quarantine_path)
    return quarantine_path


def date_range_v9_24(start: str, end: str) -> list[str]:
    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    if end_date < start_date:
        raise ValueError("end date must be >= start date")
    return [(start_date + timedelta(days=offset)).isoformat() for offset in range((end_date - start_date).days + 1)]


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
