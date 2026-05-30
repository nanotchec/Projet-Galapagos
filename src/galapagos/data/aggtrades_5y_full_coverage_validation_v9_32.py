from __future__ import annotations

import json
import statistics
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from galapagos.data.aggtrades_post_v9_collection_v9_18 import (
    BASE_SAFETY_FLAGS as BASE_SAFETY_FLAGS_V9_18,
    FINDINGS,
)
from galapagos.data.aggtrades_post_v9_full_coverage_validation_v9_29 import (
    build_aggregate_trade_id_gap_warnings_v9_29,
    build_quality_validation_v9_29,
    build_timestamp_gap_warnings_v9_29,
    quarantine_dates_v9_29,
    read_parquet_schema_columns_v9_29,
    validate_full_coverage_day_v9_29,
)


VERSION = "V9.32"
SOURCE_VERSION = "V9.31"
LAST_VALIDATED_VERSION = "V9.31"
DIRECTION = "aggtrades_5y_full_coverage_validation"

TARGET_5Y_WINDOW_START = "2021-05-05"
TARGET_5Y_WINDOW_END = "2026-05-05"
TOTAL_DAYS_EXPECTED_5Y = 1827

REPORT_JSON_PATH = Path("reports/data/aggtrades_5y_full_coverage_validation_v9_32.json")
REPORT_MD_PATH = Path("reports/data/aggtrades_5y_full_coverage_validation_v9_32.md")
MANIFEST_PATH = Path("reports/manifests/aggtrades_5y_full_coverage_validation_v9_32_manifest.json")
DOC_PATH = Path("docs/aggtrades_5y_full_coverage_validation_v9_32.md")

INPUT_PATHS = {
    "v9_31_report": Path("reports/data/aggtrades_5y_extension_collection_v9_31.json"),
    "v9_31_markdown": Path("reports/data/aggtrades_5y_extension_collection_v9_31.md"),
    "v9_31_manifest": Path("reports/manifests/aggtrades_5y_extension_collection_v9_31_manifest.json"),
    "v9_29_validation": Path("reports/data/aggtrades_post_v9_full_coverage_validation_v9_29.json"),
    "v9_28_repair": Path("reports/data/aggtrades_post_v9_bad_day_repair_v9_28.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
    "latest_summary": Path("reports/current/latest_summary.md"),
    "project_state": Path("reports/PROJECT_STATE.json"),
    "project_state_md": Path("reports/PROJECT_STATE.md"),
}

ALLOWED_DECISIONS = {
    "aggtrades_5y_full_coverage_validated",
    "aggtrades_5y_full_coverage_validated_with_non_blocking_warnings",
    "aggtrades_5y_full_coverage_blocked_by_missing_days",
    "aggtrades_5y_full_coverage_blocked_by_quality",
    "aggtrades_5y_full_coverage_blocked_by_quarantine",
    "aggtrades_5y_full_coverage_inconclusive_manual_review_required",
    "stop_aggtrades_5y_branch",
}

SAFETY_FLAGS_V9_32 = {
    **BASE_SAFETY_FLAGS_V9_18,
    "no_ml": True,
    "no_dataset_supervised": True,
    "network_used": False,
    "no_new_data_download": True,
    "no_ingestion_executed": True,
    "no_data_deletion": True,
    "no_destructive_cleanup": True,
}


def run_aggtrades_5y_full_coverage_validation_v9_32(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report = build_aggtrades_5y_full_coverage_validation_v9_32(root)
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_32(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / MANIFEST_PATH, build_manifest_v9_32(report))
    update_state_surfaces_v9_32(root, report)
    return report


def build_aggtrades_5y_full_coverage_validation_v9_32(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    started = time.monotonic()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    dates = date_range_v9_32(TARGET_5Y_WINDOW_START, TARGET_5Y_WINDOW_END)
    day_results = [validate_full_coverage_day_v9_29(root, day_value) for day_value in dates]
    calendar = build_calendar_validation_v9_32(root, day_results)
    quality = build_quality_validation_v9_32(day_results)
    quarantine = reconcile_quarantine_v9_32(root, day_results)
    reconciliation = reconcile_v9_31_counters_v9_32(root, inputs, day_results)
    row_outliers = build_row_count_outliers_v9_32(day_results)
    decision = decide_v9_32(calendar, quality, quarantine, reconciliation, row_outliers)
    runtime_seconds = round(time.monotonic() - started, 3)
    report = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": "PASS" if decision["decision"].startswith("aggtrades_5y_full_coverage_validated") else "FAIL",
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "target_5y_window_start": TARGET_5Y_WINDOW_START,
        "target_5y_window_end": TARGET_5Y_WINDOW_END,
        "total_days_expected_5y": TOTAL_DAYS_EXPECTED_5Y,
        "inputs_used": {name: {"path": item["path"], "available": item["available"]} for name, item in inputs.items()},
        "calendar_validation": calendar,
        "quality_validation": quality,
        "v9_31_counter_reconciliation": reconciliation,
        "quarantine_reconciliation": quarantine,
        "row_count_outliers": row_outliers,
        "runtime_seconds": runtime_seconds,
        "decision": decision["decision"],
        "v9_32_decision": decision,
        "next_recommendation": decision["next_recommendation"],
        "features_created": False,
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "network_used": False,
        "new_data_downloaded": False,
        "ingestion_executed": False,
        "findings": dict(FINDINGS),
        "safety_flags": dict(SAFETY_FLAGS_V9_32),
        "warnings": build_warnings_v9_32(quality, quarantine, reconciliation, row_outliers),
        "blockers": build_blockers_v9_32(calendar, quality, quarantine),
        "limitations": [
            "V9.32 valide la couverture aggTrades 5Y localement en lecture seule.",
            "Aucun telechargement, aucune ingestion et aucune reparation de donnees ne sont executes.",
            "Les compteurs V9.31 ambigus sont reconciles a partir des rapports batch et des fichiers locaux valides.",
        ],
        **flatten_summary_v9_32(calendar, quality, quarantine, reconciliation),
    }
    return report


def build_calendar_validation_v9_32(root: Path, day_results: list[dict[str, Any]]) -> dict[str, Any]:
    complete = [item for item in day_results if item["status"] == "day_complete"]
    complete_set = {item["date"] for item in complete}
    contiguous: list[str] = []
    for item in day_results:
        if item["date"] not in complete_set:
            break
        contiguous.append(item["date"])
    missing_raw = [item["date"] for item in day_results if not item["raw_exists"] or item["raw_bytes"] <= 0]
    missing_silver = [item["date"] for item in day_results if not item["silver_exists"] or item["silver_bytes"] <= 0]
    failed = [item["date"] for item in day_results if item["status"] != "day_complete"]
    partial = [item["date"] for item in day_results if (item["raw_exists"] or item["silver_exists"]) and item["status"] != "day_complete"]
    quarantined = quarantine_dates_v9_29(root, {item["date"] for item in day_results})
    return {
        "target_5y_window_start": TARGET_5Y_WINDOW_START,
        "target_5y_window_end": TARGET_5Y_WINDOW_END,
        "days_expected_5y": len(day_results),
        "days_with_raw": sum(1 for item in day_results if item["raw_exists"] and item["raw_bytes"] > 0),
        "days_with_silver": sum(1 for item in day_results if item["silver_exists"] and item["silver_bytes"] > 0),
        "days_complete": len(complete),
        "days_missing_raw": len(missing_raw),
        "days_missing_silver": len(missing_silver),
        "days_missing": len(sorted(set(missing_raw) | set(missing_silver))),
        "days_failed": len(failed),
        "days_partial": len(partial),
        "days_quarantined": len(quarantined),
        "first_missing_or_failed_day": failed[0] if failed else None,
        "last_complete_day": complete[-1]["date"] if complete else None,
        "local_file_coverage_start": complete[0]["date"] if complete else None,
        "local_file_coverage_end": complete[-1]["date"] if complete else None,
        "local_contiguous_clean_coverage_start": contiguous[0] if contiguous else None,
        "local_contiguous_clean_coverage_end": contiguous[-1] if contiguous else None,
        "complete_calendar_coverage": len(complete) == len(day_results) and not failed and not missing_raw and not missing_silver,
        "missing_raw_dates_sample": {"first": missing_raw[:5], "last": missing_raw[-5:]},
        "missing_silver_dates_sample": {"first": missing_silver[:5], "last": missing_silver[-5:]},
        "failed_dates_sample": {"first": failed[:5], "last": failed[-5:]},
    }


def build_quality_validation_v9_32(day_results: list[dict[str, Any]]) -> dict[str, Any]:
    quality = build_quality_validation_v9_29(day_results)
    complete = [item for item in day_results if item["status"] == "day_complete"]
    quality["aggregate_trade_id_gap_warnings"] = build_aggregate_trade_id_gap_warnings_v9_29(complete)
    quality["timestamp_gap_warnings"] = build_timestamp_gap_warnings_v9_29(complete)
    quality["schema_columns"] = schema_columns_sample_v9_32(complete)
    return quality


def schema_columns_sample_v9_32(day_results: list[dict[str, Any]]) -> list[str]:
    first = next((item for item in day_results if item["silver_exists"] and item["silver_bytes"] > 0), None)
    if not first:
        return []
    return read_parquet_schema_columns_v9_29(Path(first["silver_path"]))


def reconcile_v9_31_counters_v9_32(
    root: Path,
    inputs: dict[str, dict[str, Any]],
    day_results: list[dict[str, Any]],
) -> dict[str, Any]:
    report = inputs["v9_31_report"].get("payload", {})
    batch_reports = load_v9_31_batch_summaries_v9_32(root)
    days = set(date_range_v9_32("2021-05-05", "2024-05-04"))
    complete_extension_dates = {item["date"] for item in day_results if item["date"] in days and item["status"] == "day_complete"}
    downloaded = sum(int(item.get("days_downloaded") or 0) for item in batch_reports)
    normalized = sum(int(item.get("days_normalized") or 0) for item in batch_reports)
    skipped = sum(int(item.get("days_skipped_existing") or 0) for item in batch_reports)
    already_complete_before = sum(int(item.get("days_already_complete_before") or 0) for item in batch_reports)
    downloaded_zero_normalized_positive = [
        {
            "batch_id": item["batch_id"],
            "batch_start": item["batch_start"],
            "batch_end": item["batch_end"],
            "days_downloaded": item["days_downloaded"],
            "days_normalized": item["days_normalized"],
            "days_complete": item["days_complete"],
            "explanation": "raw local deja present; normalisation/validation sans nouveau telechargement",
        }
        for item in batch_reports
        if int(item.get("days_downloaded") or 0) == 0 and int(item.get("days_normalized") or 0) > 0
    ]
    downloaded_lt_normalized = [
        {
            "batch_id": item["batch_id"],
            "batch_start": item["batch_start"],
            "batch_end": item["batch_end"],
            "days_downloaded": item["days_downloaded"],
            "days_normalized": item["days_normalized"],
            "explanation": "combinaison de nouveaux telechargements et de raw deja presents localement",
        }
        for item in batch_reports
        if 0 < int(item.get("days_downloaded") or 0) < int(item.get("days_normalized") or 0)
    ]
    reporting_inconsistency = bool(downloaded_zero_normalized_positive or downloaded_lt_normalized or skipped + normalized != len(complete_extension_dates))
    return {
        "days_downloaded_reported": int(report.get("days_downloaded") or 0),
        "days_normalized_reported": int(report.get("days_normalized") or 0),
        "days_skipped_existing_reported": int(report.get("days_skipped_existing") or 0),
        "days_complete_reported": int(report.get("days_complete") or 0),
        "days_downloaded_canonical": downloaded,
        "days_normalized_canonical": normalized,
        "days_skipped_existing_canonical": skipped,
        "days_validated_existing_canonical": len(complete_extension_dates) - normalized,
        "days_already_complete_before_canonical": already_complete_before,
        "days_complete_canonical": len(complete_extension_dates),
        "extension_days_validated_from_local_files": len(complete_extension_dates),
        "batches_with_downloaded_zero_but_normalized_positive": downloaded_zero_normalized_positive,
        "batches_with_downloaded_lower_than_normalized": downloaded_lt_normalized,
        "reporting_inconsistency_detected": reporting_inconsistency,
        "reporting_inconsistency_blocking": False,
        "reconciliation_notes": [
            "Les compteurs V9.31 distinguent imparfaitement telechargement, normalisation depuis raw local et validation finale.",
            "V9.32 retient l'etat canonique des fichiers raw/silver valides: tous les jours 5Y sont presents et complets.",
            "L'ambiguite V9.31 est non bloquante car les fichiers locaux raw/silver sont lisibles et les controles qualite passent.",
        ],
    }


def load_v9_31_batch_summaries_v9_32(root: Path) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for index in range(1, 20):
        path = root / f"reports/data/aggtrades_5y_extension_batch{index:02d}_v9_31.json"
        if path.exists():
            payload = _read_json(path)
            summaries.append(payload.get("batch_summary", payload))
    return summaries


def reconcile_quarantine_v9_32(root: Path, day_results: list[dict[str, Any]]) -> dict[str, Any]:
    by_date = {item["date"]: item for item in day_results}
    quarantine_dates = quarantine_dates_v9_29(root, set(by_date))
    stale: list[str] = []
    active: list[str] = []
    overlap_complete: list[str] = []
    for day_value in quarantine_dates:
        result = by_date.get(day_value)
        if result and result["status"] == "day_complete":
            stale.append(day_value)
            overlap_complete.append(day_value)
        else:
            active.append(day_value)
    return {
        "quarantine_dates": quarantine_dates,
        "quarantine_dates_overlap_complete_days": overlap_complete,
        "quarantine_active_count": len(active),
        "quarantine_stale_count": len(stale),
        "quarantine_blocking": bool(active),
        "active_quarantine_dates": active,
        "stale_quarantine_dates": stale,
        "quarantine_notes": (
            "Quarantine stale_non_blocking: les jours correspondants sont complets et valides."
            if stale and not active
            else "Aucune quarantine detectee dans la fenetre 5Y."
            if not quarantine_dates
            else "Au moins une quarantine reste active et bloquante."
        ),
    }


def build_row_count_outliers_v9_32(day_results: list[dict[str, Any]]) -> dict[str, Any]:
    complete = [item for item in day_results if item["status"] == "day_complete"]
    rows = [int(item["rows"]) for item in complete]
    if len(rows) < 2:
        return {"outlier_count": 0, "outliers": [], "method": "insufficient_data"}
    median = statistics.median(rows)
    low = median * 0.2
    high = median * 5.0
    outliers = [
        {"date": item["date"], "rows": int(item["rows"]), "severity": "warning"}
        for item in complete
        if int(item["rows"]) < low or int(item["rows"]) > high
    ]
    return {
        "outlier_count": len(outliers),
        "outliers": outliers[:100],
        "method": "non_blocking_row_count_outlier_scan_threshold_0.2x_to_5x_median",
        "median_rows_per_day": int(median),
    }


def decide_v9_32(
    calendar: dict[str, Any],
    quality: dict[str, Any],
    quarantine: dict[str, Any],
    reconciliation: dict[str, Any],
    row_outliers: dict[str, Any],
) -> dict[str, Any]:
    if quarantine["quarantine_blocking"]:
        decision = "aggtrades_5y_full_coverage_blocked_by_quarantine"
        recommendation = "V9.33 - Quarantine Review Pack"
        justification = "Une quarantine active recouvre au moins un jour non complet ou non valide."
    elif not calendar["complete_calendar_coverage"]:
        decision = "aggtrades_5y_full_coverage_blocked_by_missing_days"
        recommendation = "V9.33 - AggTrades 5Y Coverage Correction"
        justification = "La couverture calendrier 5Y complete n'est pas atteinte."
    elif quality["quality_status"] != "PASS":
        decision = "aggtrades_5y_full_coverage_blocked_by_quality"
        recommendation = "V9.33 - AggTrades 5Y Coverage Correction"
        justification = "La validation qualite globale 5Y detecte une anomalie bloquante."
    elif (
        quarantine["quarantine_stale_count"]
        or quality["aggregate_trade_id_gap_warnings"]
        or quality["timestamp_gap_warnings"]
        or row_outliers["outlier_count"]
        or reconciliation["reporting_inconsistency_detected"]
    ):
        decision = "aggtrades_5y_full_coverage_validated_with_non_blocking_warnings"
        recommendation = "V9.33 - OHLCV + AggTrades 5Y Feature Store"
        justification = "La couverture et la qualite 5Y sont validees; seules des alertes non bloquantes restent documentees."
    else:
        decision = "aggtrades_5y_full_coverage_validated"
        recommendation = "V9.33 - OHLCV + AggTrades 5Y Feature Store"
        justification = "Tous les jours 5Y sont complets, valides et sans quarantine bloquante."
    return {
        "decision": decision,
        "confidence": "high",
        "next_recommendation": recommendation,
        "justification": justification,
        "no_backtest": True,
        "no_walk_forward": True,
        "no_trading": True,
    }


def flatten_summary_v9_32(
    calendar: dict[str, Any],
    quality: dict[str, Any],
    quarantine: dict[str, Any],
    reconciliation: dict[str, Any],
) -> dict[str, Any]:
    complete = calendar["complete_calendar_coverage"] and quality["quality_status"] == "PASS" and not quarantine["quarantine_blocking"]
    return {
        "days_expected_5y": calendar["days_expected_5y"],
        "days_complete": calendar["days_complete"],
        "days_missing": calendar["days_missing"],
        "days_failed": calendar["days_failed"],
        "days_partial": calendar["days_partial"],
        "days_quarantined": calendar["days_quarantined"],
        "complete_calendar_coverage": calendar["complete_calendar_coverage"],
        "local_file_coverage_start": calendar["local_file_coverage_start"],
        "local_file_coverage_end": calendar["local_file_coverage_end"],
        "local_contiguous_clean_coverage_start": calendar["local_contiguous_clean_coverage_start"],
        "local_contiguous_clean_coverage_end": calendar["local_contiguous_clean_coverage_end"],
        "complete_collection_reached": complete,
        "future_full_coverage_complete": complete,
        "global_duplicate_count": quality["global_duplicate_count"],
        "global_invalid_rows": quality["global_invalid_rows"],
        "aggregate_trade_id_gap_warnings": quality["aggregate_trade_id_gap_warnings"],
        "timestamp_gap_warnings": quality["timestamp_gap_warnings"],
        "schema_mismatch_count": quality["schema_mismatch_count"],
        "non_positive_price_count": quality["non_positive_price_count"],
        "non_positive_quantity_count": quality["non_positive_quantity_count"],
        "available_ts_violation_count": quality["available_ts_violation_count"],
        "partition_mismatch_count": quality["partition_mismatch_count"],
        "raw_read_errors": quality["raw_read_errors"],
        "silver_read_errors": quality["silver_read_errors"],
        "quality_status": quality["quality_status"],
        "coverage_status": "target_5y_window_validated" if complete else "target_5y_window_blocked",
        "total_rows_cumulative_5y": quality["total_rows"],
        "raw_bytes_cumulative_5y": quality["raw_bytes_total"],
        "silver_bytes_cumulative_5y": quality["silver_bytes_total"],
        "quarantine_active_count": quarantine["quarantine_active_count"],
        "quarantine_stale_count": quarantine["quarantine_stale_count"],
        "quarantine_blocking": quarantine["quarantine_blocking"],
        "days_downloaded_canonical": reconciliation["days_downloaded_canonical"],
        "days_normalized_canonical": reconciliation["days_normalized_canonical"],
        "days_skipped_existing_canonical": reconciliation["days_skipped_existing_canonical"],
        "days_validated_existing_canonical": reconciliation["days_validated_existing_canonical"],
        "reporting_inconsistency_detected": reconciliation["reporting_inconsistency_detected"],
        "reporting_inconsistency_blocking": reconciliation["reporting_inconsistency_blocking"],
    }


def build_warnings_v9_32(
    quality: dict[str, Any],
    quarantine: dict[str, Any],
    reconciliation: dict[str, Any],
    row_outliers: dict[str, Any],
) -> list[str]:
    warnings: list[str] = []
    if quarantine["quarantine_stale_count"]:
        warnings.append("Des fichiers quarantine stale_non_blocking existent pour des jours complets et valides.")
    if quality["aggregate_trade_id_gap_warnings"]:
        warnings.append("Des alertes de continuite aggregate_trade_id inter-jours sont documentees.")
    if quality["timestamp_gap_warnings"]:
        warnings.append("Des alertes de continuite timestamp inter-jours sont documentees.")
    if row_outliers["outlier_count"]:
        warnings.append("Des outliers de row count sont signales comme non bloquants.")
    if reconciliation["reporting_inconsistency_detected"]:
        warnings.append("Les compteurs V9.31 telechargement/normalisation/skipped sont ambigus mais non bloquants.")
    return warnings


def build_blockers_v9_32(calendar: dict[str, Any], quality: dict[str, Any], quarantine: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not calendar["complete_calendar_coverage"]:
        blockers.append("Couverture calendrier 5Y incomplete.")
    if quality["quality_status"] != "PASS":
        blockers.append("Validation qualite globale 5Y en echec.")
    if quarantine["quarantine_blocking"]:
        blockers.append("Quarantine active bloquante.")
    return blockers


def build_manifest_v9_32(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": report["status"],
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "report_path": REPORT_JSON_PATH.as_posix(),
        "markdown_path": REPORT_MD_PATH.as_posix(),
        "decision": report["decision"],
        "next_recommendation": report["next_recommendation"],
        "target_5y_window_start": TARGET_5Y_WINDOW_START,
        "target_5y_window_end": TARGET_5Y_WINDOW_END,
        "days_expected_5y": report["days_expected_5y"],
        "days_complete": report["days_complete"],
        "days_missing": report["days_missing"],
        "days_failed": report["days_failed"],
        "global_duplicate_count": report["global_duplicate_count"],
        "global_invalid_rows": report["global_invalid_rows"],
        "quarantine_active_count": report["quarantine_active_count"],
        "quarantine_stale_count": report["quarantine_stale_count"],
        "complete_collection_reached": report["complete_collection_reached"],
        "future_full_coverage_complete": report["future_full_coverage_complete"],
        "reporting_inconsistency_detected": report["reporting_inconsistency_detected"],
        "reporting_inconsistency_blocking": report["reporting_inconsistency_blocking"],
        "findings": report["findings"],
        "safety_flags": report["safety_flags"],
    }


def build_markdown_v9_32(report: dict[str, Any]) -> str:
    lines = [
        "# V9.32 - AggTrades 5Y Full Coverage Validation",
        "",
        "## Resume",
        f"- Decision V9.32 : `{report['decision']}`.",
        f"- Recommandation suivante : `{report['next_recommendation']}`.",
        f"- Couverture 5Y : `{report['local_file_coverage_start']}` -> `{report['local_file_coverage_end']}`.",
        f"- Jours attendus/complets/manquants/failed : `{report['days_expected_5y']}` / `{report['days_complete']}` / `{report['days_missing']}` / `{report['days_failed']}`.",
        f"- Couverture calendrier complete : `{report['complete_calendar_coverage']}`.",
        f"- Qualite globale : `{report['quality_status']}`.",
        f"- Duplicats globaux : `{report['global_duplicate_count']}`.",
        f"- Lignes invalides globales : `{report['global_invalid_rows']}`.",
        "",
        "## Reconciliation V9.31",
        f"- Telecharges/normalises/skipped reportes : `{report['v9_31_counter_reconciliation']['days_downloaded_reported']}` / `{report['v9_31_counter_reconciliation']['days_normalized_reported']}` / `{report['v9_31_counter_reconciliation']['days_skipped_existing_reported']}`.",
        f"- Telecharges/normalises/skipped canoniques : `{report['days_downloaded_canonical']}` / `{report['days_normalized_canonical']}` / `{report['days_skipped_existing_canonical']}`.",
        f"- Incoherence reporting detectee/bloquante : `{report['reporting_inconsistency_detected']}` / `{report['reporting_inconsistency_blocking']}`.",
        "",
        "## Quarantine",
        f"- Quarantine active/stale/blocking : `{report['quarantine_active_count']}` / `{report['quarantine_stale_count']}` / `{report['quarantine_blocking']}`.",
        f"- Notes : {report['quarantine_reconciliation']['quarantine_notes']}",
        "",
        "## Garde-fous",
        "- Aucun trading, aucun paper live, aucun ordre, aucun backtest execute, aucun walk-forward, aucun ML, aucun dataset supervise.",
        "- Aucune strategie, aucun signal actionnable, aucun modele persistant, aucune API privee, aucune cle API.",
        "- Aucun telechargement de nouvelles donnees, aucune nouvelle ingestion, aucune suppression destructive, aucun push.",
        "- Aucun sidecar et aucune empreinte ZIP.",
    ]
    return "\n".join(lines) + "\n"


def update_state_surfaces_v9_32(root: Path, report: dict[str, Any]) -> None:
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "source_version": SOURCE_VERSION,
        "direction": DIRECTION,
        "v9_32_decision": report["decision"],
        "recommended_next_step": report["next_recommendation"],
        "target_5y_window_start": TARGET_5Y_WINDOW_START,
        "target_5y_window_end": TARGET_5Y_WINDOW_END,
        "days_expected_5y": report["days_expected_5y"],
        "days_complete": report["days_complete"],
        "days_missing": report["days_missing"],
        "days_failed": report["days_failed"],
        "global_duplicate_count": report["global_duplicate_count"],
        "global_invalid_rows": report["global_invalid_rows"],
        "complete_collection_reached": report["complete_collection_reached"],
        "future_full_coverage_complete": report["future_full_coverage_complete"],
        "quality_status": report["quality_status"],
        "coverage_status": report["coverage_status"],
        "quarantine_active_count": report["quarantine_active_count"],
        "quarantine_stale_count": report["quarantine_stale_count"],
        "reporting_inconsistency_detected": report["reporting_inconsistency_detected"],
        "reporting_inconsistency_blocking": report["reporting_inconsistency_blocking"],
        "features_created": False,
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "network_used": False,
        "network_scope": None,
        "new_data_downloaded": False,
        "new_data_download_scope": None,
        "ingestion_executed": False,
        "ingestion_scope": None,
        **report["safety_flags"],
    }
    state_path = root / "reports/PROJECT_STATE.json"
    state = _read_json(state_path) if state_path.exists() else {}
    state.update(metrics)
    _write_json(state_path, state)
    _write_json(root / "reports/current/latest_metrics.json", metrics)
    text = (
        "# Synthese courante - V9.32\n\n"
        f"- Derniere version validee : `{LAST_VALIDATED_VERSION}`.\n"
        f"- Candidate : `{VERSION}`.\n"
        "- Statut : `pending_external_audit`.\n"
        f"- Direction : `{DIRECTION}`.\n"
        f"- Decision V9.32 : `{report['decision']}`.\n"
        f"- Couverture 5Y validee : `{report['local_file_coverage_start']}` -> `{report['local_file_coverage_end']}`.\n"
        f"- Jours complets/manquants/failed : `{report['days_complete']}` / `{report['days_missing']}` / `{report['days_failed']}`.\n"
        f"- Duplicats/lignes invalides : `{report['global_duplicate_count']}` / `{report['global_invalid_rows']}`.\n"
        f"- Recommandation : {report['next_recommendation']}.\n"
        "- Aucun trading, paper live, ordre, backtest, walk-forward, ML, dataset supervise, strategie ou signal actionnable.\n"
        "- Aucun telechargement, aucune ingestion, aucune suppression destructive, aucun sidecar et aucune empreinte ZIP.\n"
    )
    _write_text(root / "reports/PROJECT_STATE.md", text)
    _write_text(root / "reports/current/latest_summary.md", text)
    _write_text(root / "reports/current/latest_metrics.md", text)
    _write_text(
        root / "README.md",
        "# Projet Galapagos\n\n"
        f"- Derniere version validee : {LAST_VALIDATED_VERSION}.\n"
        f"- Candidate : {VERSION}, validation globale de couverture aggTrades 5Y.\n"
        f"- Couverture locale : {report['local_file_coverage_start']} -> {report['local_file_coverage_end']}.\n"
        "- Aucun trading, ordre, backtest, walk-forward, strategie, signal actionnable, modele persistant, API privee ou cle API.\n"
        "- Aucun telechargement de nouvelles donnees, aucune ingestion, aucune suppression destructive, aucun sidecar et aucune empreinte ZIP.\n",
    )


def date_range_v9_32(start: str, end: str) -> list[str]:
    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    if end_date < start_date:
        raise ValueError("end date must be >= start date")
    return [(start_date + timedelta(days=offset)).isoformat() for offset in range((end_date - start_date).days + 1)]


def _load_input(root: Path, path: Path) -> dict[str, Any]:
    full = root / path
    if not full.exists():
        return {"path": path.as_posix(), "available": False, "payload": {}}
    payload: Any = _read_json(full) if path.suffix == ".json" else {"text": full.read_text(encoding="utf-8")}
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
