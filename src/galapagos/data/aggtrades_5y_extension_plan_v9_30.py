from __future__ import annotations

import json
import os
import subprocess
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from galapagos.data.aggtrades_post_v9_collection_v9_18 import FINDINGS, MARKET_TYPE, PUBLIC_ARCHIVE_HOST, SYMBOL, TRADE_SOURCE_TYPE, VENUE


VERSION = "V9.30"
SOURCE_VERSION = "V9.29"
LAST_VALIDATED_VERSION = "V9.29"
DIRECTION = "aggtrades_5y_historical_extension_plan"

CURRENT_VALIDATED_WINDOW_START = "2024-05-05"
CURRENT_VALIDATED_WINDOW_END = "2026-05-05"
TARGET_5Y_WINDOW_START = "2021-05-05"
TARGET_5Y_WINDOW_END = "2026-05-05"
EXTENSION_WINDOW_START = "2021-05-05"
EXTENSION_WINDOW_END = "2024-05-04"
SAFETY_MARGIN_FACTOR = 1.3
RESERVE_GIB = 40.0
MAX_BATCH_DAYS = 90

REPORT_JSON_PATH = Path("reports/data/aggtrades_5y_extension_plan_v9_30.json")
REPORT_MD_PATH = Path("reports/data/aggtrades_5y_extension_plan_v9_30.md")
MANIFEST_PATH = Path("reports/manifests/aggtrades_5y_extension_plan_v9_30_manifest.json")
DOC_PATH = Path("docs/aggtrades_5y_extension_plan_v9_30.md")

INPUT_PATHS = {
    "v9_29_report": Path("reports/data/aggtrades_post_v9_full_coverage_validation_v9_29.json"),
    "v9_29_markdown": Path("reports/data/aggtrades_post_v9_full_coverage_validation_v9_29.md"),
    "v9_29_manifest": Path("reports/manifests/aggtrades_post_v9_full_coverage_validation_v9_29_manifest.json"),
    "v9_28_report": Path("reports/data/aggtrades_post_v9_bad_day_repair_v9_28.json"),
    "v9_27_report": Path("reports/data/aggtrades_post_v9_storage_recheck_resume_v9_27.json"),
    "v9_26_report": Path("reports/data/aggtrades_post_v9_storage_resume_campaign_v9_26.json"),
    "v9_25_1_report": Path("reports/data/aggtrades_post_v9_resume_campaign_v9_25_1.json"),
    "v9_24_report": Path("reports/data/aggtrades_post_v9_batch3_collection_v9_24.json"),
    "v9_23_report": Path("reports/data/aggtrades_post_v9_batch2_collection_v9_23.json"),
    "v9_21_report": Path("reports/data/aggtrades_post_v9_batch_expansion_v9_21.json"),
    "v9_20_report": Path("reports/data/aggtrades_post_v9_batch_collection_v9_20.json"),
    "v9_19_report": Path("reports/data/aggtrades_post_v9_pilot_collection_v9_19.json"),
    "v8_2_manifest": Path("reports/manifests/public_trades_1y_window_v8_2_manifest.json"),
    "v5_0_manifest": Path("reports/manifests/max_history_public_market_data_v5_0_manifest.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
    "latest_summary": Path("reports/current/latest_summary.md"),
    "project_state": Path("reports/PROJECT_STATE.json"),
    "project_state_md": Path("reports/PROJECT_STATE.md"),
}

ALLOWED_DECISIONS = {
    "aggtrades_5y_extension_plan_ready",
    "aggtrades_5y_extension_plan_ready_with_storage_warning",
    "aggtrades_5y_extension_not_ready_storage_blocker",
    "aggtrades_5y_extension_not_ready_source_uncertainty",
    "aggtrades_5y_extension_not_recommended",
    "stop_aggtrades_5y_extension_branch",
}

SAFETY_FLAGS_V9_30 = {
    "no_trading": True,
    "no_paper_live": True,
    "no_orders": True,
    "no_backtest": True,
    "no_walk_forward": True,
    "no_ml": True,
    "no_dataset_supervised": True,
    "no_strategy": True,
    "no_actionable_signal": True,
    "no_persistent_model": True,
    "api_key_used": False,
    "private_endpoint_used": False,
    "exchange_auth_used": False,
    "websocket_live_used": False,
    "network_used": False,
    "no_new_data_download": True,
    "no_ingestion_executed": True,
    "no_data_deletion": True,
    "no_destructive_cleanup": True,
    "no_sidecars": True,
    "no_zip_fingerprints": True,
}


def run_aggtrades_5y_extension_plan_v9_30(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report = build_aggtrades_5y_extension_plan_v9_30(root)
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_30(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / MANIFEST_PATH, build_manifest_v9_30(report))
    update_state_surfaces_v9_30(root, report)
    return report


def build_aggtrades_5y_extension_plan_v9_30(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    current = build_current_validated_window_v9_30(inputs)
    target = build_target_5y_window_v9_30()
    estimated = estimate_volume_v9_30(current, target)
    disk = build_disk_preflight_v9_30(root, estimated)
    source = build_source_availability_assessment_v9_30()
    collection_plan = build_collection_plan_v9_31(target, estimated, disk)
    validation_plan = build_validation_plan_v9_32()
    roadmap = build_roadmap_after_5y_v9_30()
    decision = decide_v9_30(disk, source)
    report = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": "PASS" if decision["decision"].startswith("aggtrades_5y_extension_plan_ready") else "WARN",
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "mode": "plan-only",
        "inputs_used": {name: {"path": item["path"], "available": item["available"]} for name, item in inputs.items()},
        "current_validated_window": current,
        "target_5y_window": target,
        "extension_window": target["extension_window"],
        "extension_days_needed": target["extension_days_needed"],
        "estimated_volume": estimated,
        "disk_preflight": disk,
        "source_availability_assessment": source,
        "collection_plan_v9_31": collection_plan,
        "validation_plan_v9_32": validation_plan,
        "roadmap_after_5y": roadmap,
        "decision": decision["decision"],
        "v9_30_decision": decision,
        "next_recommendation": decision["next_recommendation"],
        "blockers": decision["blockers"],
        "warnings": build_warnings_v9_30(disk, source),
        "limitations": [
            "V9.30 est plan-only: aucun reseau, aucun telechargement, aucune ingestion et aucune reparation ne sont executes.",
            "La disponibilite exacte des fichiers Binance 2021-2024 doit etre confirmee pendant la collecte V9.31.",
            "Les estimations utilisent les moyennes V9.29; les regimes de marche 2021-2024 peuvent produire des volumes differents.",
        ],
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
        "safety_flags": dict(SAFETY_FLAGS_V9_30),
        **flatten_summary_v9_30(current, target, estimated, disk, decision),
    }
    return report


def build_current_validated_window_v9_30(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    payload = inputs["v9_29_report"].get("payload", {})
    validated_days = int(payload.get("days_complete") or payload.get("days_expected") or 731)
    rows = int(payload.get("total_rows_cumulative") or 0)
    raw_bytes = int(payload.get("raw_bytes_cumulative") or 0)
    silver_bytes = int(payload.get("silver_bytes_cumulative") or 0)
    return {
        "validated_window_start": CURRENT_VALIDATED_WINDOW_START,
        "validated_window_end": CURRENT_VALIDATED_WINDOW_END,
        "validated_days": validated_days,
        "validated_rows": rows,
        "validated_raw_bytes": raw_bytes,
        "validated_silver_bytes": silver_bytes,
        "average_rows_per_day": rows // validated_days,
        "average_raw_bytes_per_day": raw_bytes // validated_days,
        "average_silver_bytes_per_day": silver_bytes // validated_days,
        "quality_status": payload.get("quality_status", "PASS"),
        "coverage_status": payload.get("coverage_status", "target_window_validated"),
        "complete_collection_reached": payload.get("complete_collection_reached") is True,
        "future_full_coverage_complete": payload.get("future_full_coverage_complete") is True,
        "quarantine_status": {
            "quarantine_active_count": int(payload.get("quarantine_active_count") or 0),
            "quarantine_stale_count": int(payload.get("quarantine_stale_count") or 0),
            "quarantine_blocking": payload.get("quarantine_blocking") is True,
            "quarantine_notes": "stale_non_blocking" if int(payload.get("quarantine_stale_count") or 0) else "none",
        },
        "validated_by": SOURCE_VERSION,
        "local_files_present_assumption": "V9.30 inspecte seulement les metadonnees legeres et s'appuie sur la validation exhaustive V9.29.",
    }


def build_target_5y_window_v9_30() -> dict[str, Any]:
    target_days = len(date_range_v9_30(TARGET_5Y_WINDOW_START, TARGET_5Y_WINDOW_END))
    validated_days = len(date_range_v9_30(CURRENT_VALIDATED_WINDOW_START, CURRENT_VALIDATED_WINDOW_END))
    extension_days = len(date_range_v9_30(EXTENSION_WINDOW_START, EXTENSION_WINDOW_END))
    return {
        "target_5y_window_start": TARGET_5Y_WINDOW_START,
        "target_5y_window_end": TARGET_5Y_WINDOW_END,
        "target_5y_days_expected": target_days,
        "current_validated_window_start": CURRENT_VALIDATED_WINDOW_START,
        "current_validated_window_end": CURRENT_VALIDATED_WINDOW_END,
        "already_validated_days": validated_days,
        "extension_window": {"extension_window_start": EXTENSION_WINDOW_START, "extension_window_end": EXTENSION_WINDOW_END},
        "extension_days_needed": extension_days,
        "overlap_days": 0,
        "gaps_expected": [],
        "no_recollection_required_for_validated_window": True,
    }


def estimate_volume_v9_30(current: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    extension_days = int(target["extension_days_needed"])
    target_days = int(target["target_5y_days_expected"])
    avg_rows = int(current["average_rows_per_day"])
    avg_raw = int(current["average_raw_bytes_per_day"])
    avg_silver = int(current["average_silver_bytes_per_day"])
    extension_raw = avg_raw * extension_days
    extension_silver = avg_silver * extension_days
    extension_total = extension_raw + extension_silver
    target_raw = avg_raw * target_days
    target_silver = avg_silver * target_days
    target_total = target_raw + target_silver
    required = int(extension_total * SAFETY_MARGIN_FACTOR)
    return {
        "basis": "V9.29 validated averages",
        "validated_average_rows_per_day": avg_rows,
        "validated_average_raw_bytes_per_day": avg_raw,
        "validated_average_silver_bytes_per_day": avg_silver,
        "estimated_extension_rows": avg_rows * extension_days,
        "estimated_extension_raw_bytes": extension_raw,
        "estimated_extension_silver_bytes": extension_silver,
        "estimated_extension_total_bytes": extension_total,
        "estimated_target_5y_rows": avg_rows * target_days,
        "estimated_target_5y_raw_bytes": target_raw,
        "estimated_target_5y_silver_bytes": target_silver,
        "estimated_target_5y_total_bytes": target_total,
        "safety_margin_factor": SAFETY_MARGIN_FACTOR,
        "required_free_bytes_for_extension": required,
        "required_free_gib_for_extension": round(required / 1024**3, 3),
        "recommended_free_gib_before_collection": round(required / 1024**3 + RESERVE_GIB, 3),
    }


def build_disk_preflight_v9_30(root: Path, estimated: dict[str, Any]) -> dict[str, Any]:
    project_path = root
    data_path = root / "data"
    project_stat = statvfs_free_v9_30(project_path)
    data_stat = statvfs_free_v9_30(data_path if data_path.exists() else project_path)
    free_gib = min(project_stat["free_gib"], data_stat["free_gib"])
    recommended = float(estimated["recommended_free_gib_before_collection"])
    safe = free_gib >= recommended
    if free_gib < float(estimated["required_free_gib_for_extension"]):
        level = "blocker"
        batch = 0
    elif free_gib < recommended:
        level = "warning"
        batch = 30
    elif free_gib < 180:
        level = "comfortable_with_checkpoints"
        batch = 60
    else:
        level = "comfortable"
        batch = 90
    return {
        "project_path": project_path.as_posix(),
        "data_path": data_path.as_posix(),
        "df_h_project_output": run_local_command_v9_30(["df", "-h", project_path.as_posix()]),
        "df_h_data_output": run_local_command_v9_30(["df", "-h", data_path.as_posix()]),
        "df_g_data_output": run_local_command_v9_30(["df", "-g", data_path.as_posix()]),
        "statvfs_project": project_stat,
        "statvfs_data": data_stat,
        "free_gib_project_mount": project_stat["free_gib"],
        "free_gib_data_mount": data_stat["free_gib"],
        "safe_for_5y_extension_collection": safe,
        "storage_warning_level": level,
        "collection_batch_size_recommendation": batch,
        "required_free_bytes_for_extension": estimated["required_free_bytes_for_extension"],
        "required_free_gib_for_extension": estimated["required_free_gib_for_extension"],
        "recommended_free_gib_before_collection": recommended,
        "storage_notes": "Les lots doivent verifier l'espace avant chaque batch; V9.30 ne supprime et ne compresse aucune donnee.",
    }


def build_source_availability_assessment_v9_30() -> dict[str, Any]:
    pattern = f"https://{PUBLIC_ARCHIVE_HOST}/data/spot/daily/aggTrades/{SYMBOL}/{SYMBOL}-aggTrades-YYYY-MM-DD.zip"
    return {
        "source_name": "Binance public archive aggTrades daily",
        "host": PUBLIC_ARCHIVE_HOST,
        "market_type": MARKET_TYPE,
        "symbol": SYMBOL,
        "venue": VENUE,
        "trade_source_type": TRADE_SOURCE_TYPE,
        "historical_availability_assumption": "probable_for_btcusdt_spot_aggtrades_but_not_verified_by_v9_30",
        "availability_needs_confirmation": True,
        "network_check_required_in_future_collection": True,
        "expected_url_pattern": pattern,
        "schema_compatibility_assessment": "Le schema bronze/silver actuel peut etre conserve si les CSV historiques gardent les colonnes Binance aggTrades attendues.",
        "known_risks": [
            "Disponibilite exacte des fichiers 2021-2024 non verifiee sans reseau.",
            "Possibles jours manquants ou archives corrompues dans l'historique ancien.",
            "Volumes de trades 2021-2024 potentiellement differents des moyennes 2024-2026.",
            "Doublons exacts ou anomalies d'ordre aggregate_trade_id similaires au cas 2026-02-11.",
        ],
        "source_risk_level": "medium_until_v9_31_confirms_files",
    }


def build_collection_plan_v9_31(target: dict[str, Any], estimated: dict[str, Any], disk: dict[str, Any]) -> list[dict[str, Any]]:
    batch_size = int(disk["collection_batch_size_recommendation"] or 30)
    if batch_size <= 0:
        batch_size = 30
    dates = date_range_v9_30(EXTENSION_WINDOW_START, EXTENSION_WINDOW_END)
    batches: list[dict[str, Any]] = []
    avg_rows = int(estimated["validated_average_rows_per_day"])
    avg_raw = int(estimated["validated_average_raw_bytes_per_day"])
    avg_silver = int(estimated["validated_average_silver_bytes_per_day"])
    for index, offset in enumerate(range(0, len(dates), batch_size), start=1):
        chunk = dates[offset : offset + batch_size]
        expected_days = len(chunk)
        batches.append(
            {
                "batch_id": f"V9.31_batch_{index:02d}",
                "start_date": chunk[0],
                "end_date": chunk[-1],
                "max_downloads": expected_days,
                "expected_days": expected_days,
                "estimated_raw_bytes": avg_raw * expected_days,
                "estimated_silver_bytes": avg_silver * expected_days,
                "estimated_rows": avg_rows * expected_days,
                "checkpoint_required": True,
                "storage_check_before_batch": True,
                "audit_required_after_batch": False,
                "skip_existing_complete_days": True,
                "overwrite_complete_days": False,
                "quarantine_on_failure": True,
            }
        )
    return batches


def build_validation_plan_v9_32() -> dict[str, Any]:
    return {
        "version": "V9.32",
        "scope": "aggtrades_5y_full_coverage_validation",
        "target_window_start": TARGET_5Y_WINDOW_START,
        "target_window_end": TARGET_5Y_WINDOW_END,
        "checks": [
            "raw_and_silver_presence",
            "missing_days",
            "duplicate_aggregate_trade_id",
            "invalid_rows",
            "timestamps_utc",
            "partition_date_matches_event_ts",
            "available_ts_gte_event_ts",
            "aggregate_trade_id_continuity_warnings",
            "volume_and_row_count_anomalies",
            "quarantine_stale_or_active_reconciliation",
            "schema_stability",
            "global_manifest",
        ],
        "allowed_decisions": [
            "aggtrades_5y_full_coverage_validated",
            "aggtrades_5y_full_coverage_validated_with_non_blocking_warnings",
            "aggtrades_5y_full_coverage_blocked_by_missing_days",
            "aggtrades_5y_full_coverage_blocked_by_quality",
            "aggtrades_5y_full_coverage_inconclusive_manual_review_required",
        ],
    }


def build_roadmap_after_5y_v9_30() -> list[dict[str, str]]:
    return [
        {"version": "V9.31", "title": "AggTrades 5Y Historical Extension Collection"},
        {"version": "V9.32", "title": "AggTrades 5Y Full Coverage Validation"},
        {"version": "V9.33", "title": "OHLCV + AggTrades 5Y Feature Store"},
        {"version": "V9.34", "title": "5Y Dataset"},
        {"version": "V9.35", "title": "5Y ML Offline"},
        {"version": "V9.36", "title": "5Y Strict Walk-Forward"},
        {"version": "V9.37", "title": "5Y Research Decision Gate"},
        {"version": "post_v9_37", "title": "Funding / open interest, liquidations, order book L2 only after the decision gate"},
    ]


def decide_v9_30(disk: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    if disk["storage_warning_level"] == "blocker":
        decision = "aggtrades_5y_extension_not_ready_storage_blocker"
        recommendation = "V9.31 - Storage Remediation Plan"
        blockers = ["free disk below required extension estimate"]
    elif source["source_risk_level"] == "high":
        decision = "aggtrades_5y_extension_not_ready_source_uncertainty"
        recommendation = "V9.31 - Historical Source Availability Probe"
        blockers = ["source uncertainty too high"]
    elif disk["storage_warning_level"] == "warning":
        decision = "aggtrades_5y_extension_plan_ready_with_storage_warning"
        recommendation = "V9.31 - Storage Review then AggTrades 5Y Collection"
        blockers = []
    else:
        decision = "aggtrades_5y_extension_plan_ready"
        recommendation = "V9.31 - AggTrades 5Y Historical Extension Collection"
        blockers = []
    return {
        "decision": decision,
        "next_recommendation": recommendation,
        "blockers": blockers,
        "no_backtest": True,
        "no_trading": True,
        "no_signal": True,
        "justification": "Plan faisable en lots controles; disponibilite historique a confirmer durant V9.31 sans pretendre une existence non verifiee en V9.30.",
    }


def build_warnings_v9_30(disk: dict[str, Any], source: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if disk["storage_warning_level"] in {"warning", "comfortable_with_checkpoints"}:
        warnings.append("L'espace disque reste a verifier avant chaque lot V9.31.")
    if source["availability_needs_confirmation"]:
        warnings.append("La disponibilite exacte des fichiers 2021-2024 doit etre confirmee par la collecte V9.31.")
    return warnings


def flatten_summary_v9_30(current: dict[str, Any], target: dict[str, Any], estimated: dict[str, Any], disk: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    return {
        "validated_window_start": current["validated_window_start"],
        "validated_window_end": current["validated_window_end"],
        "validated_days": current["validated_days"],
        "validated_rows": current["validated_rows"],
        "validated_raw_bytes": current["validated_raw_bytes"],
        "validated_silver_bytes": current["validated_silver_bytes"],
        "target_5y_window_start": target["target_5y_window_start"],
        "target_5y_window_end": target["target_5y_window_end"],
        "target_5y_days_expected": target["target_5y_days_expected"],
        "already_validated_days": target["already_validated_days"],
        "extension_window_start": EXTENSION_WINDOW_START,
        "extension_window_end": EXTENSION_WINDOW_END,
        "extension_days_needed": target["extension_days_needed"],
        "estimated_extension_rows": estimated["estimated_extension_rows"],
        "estimated_extension_raw_bytes": estimated["estimated_extension_raw_bytes"],
        "estimated_extension_silver_bytes": estimated["estimated_extension_silver_bytes"],
        "estimated_extension_total_bytes": estimated["estimated_extension_total_bytes"],
        "required_free_gib_for_extension": estimated["required_free_gib_for_extension"],
        "recommended_free_gib_before_collection": estimated["recommended_free_gib_before_collection"],
        "free_gib_data_mount": disk["free_gib_data_mount"],
        "free_gib_project_mount": disk["free_gib_project_mount"],
        "safe_for_5y_extension_collection": disk["safe_for_5y_extension_collection"],
        "storage_warning_level": disk["storage_warning_level"],
        "collection_batch_size_recommendation": disk["collection_batch_size_recommendation"],
        "v9_30_decision_name": decision["decision"],
    }


def build_manifest_v9_30(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": report["status"],
        "created_at_utc": _utc_now(),
        "report_path": REPORT_JSON_PATH.as_posix(),
        "markdown_path": REPORT_MD_PATH.as_posix(),
        "decision": report["decision"],
        "next_recommendation": report["next_recommendation"],
        "extension_days_needed": report["extension_days_needed"],
        "estimated_extension_total_bytes": report["estimated_extension_total_bytes"],
        "safe_for_5y_extension_collection": report["safe_for_5y_extension_collection"],
        "safety_flags": report["safety_flags"],
        "findings": report["findings"],
    }


def build_markdown_v9_30(report: dict[str, Any]) -> str:
    batches = report["collection_plan_v9_31"]
    lines = [
        "# V9.30 - AggTrades 5Y Historical Extension Plan",
        "",
        "## Resume",
        f"- Decision V9.30 : `{report['decision']}`.",
        f"- Recommandation suivante : `{report['next_recommendation']}`.",
        f"- Fenetre validee actuelle : `{report['validated_window_start']}` -> `{report['validated_window_end']}`.",
        f"- Fenetre cible 5Y : `{report['target_5y_window_start']}` -> `{report['target_5y_window_end']}`.",
        f"- Fenetre a collecter : `{report['extension_window_start']}` -> `{report['extension_window_end']}`.",
        f"- Jours deja valides / a collecter : `{report['already_validated_days']}` / `{report['extension_days_needed']}`.",
        f"- Estimation extension raw/silver : `{report['estimated_extension_raw_bytes']}` / `{report['estimated_extension_silver_bytes']}` bytes.",
        f"- Espace libre data/project : `{report['free_gib_data_mount']}` / `{report['free_gib_project_mount']}` GiB.",
        f"- Safe pour collecte 5Y : `{report['safe_for_5y_extension_collection']}`.",
        "",
        "## Source",
        f"- Source : `{report['source_availability_assessment']['source_name']}`.",
        f"- Host : `{report['source_availability_assessment']['host']}`.",
        "- Disponibilite historique 2021-2024 : probable mais non verifiee par V9.30; confirmation requise en V9.31.",
        "",
        "## Plan V9.31",
        f"- Lots proposes : `{len(batches)}`.",
        f"- Taille max recommandee : `{report['collection_batch_size_recommendation']}` jours.",
        f"- Premier lot : `{batches[0]['start_date']}` -> `{batches[0]['end_date']}`.",
        f"- Dernier lot : `{batches[-1]['start_date']}` -> `{batches[-1]['end_date']}`.",
        "",
        "## Plan V9.32",
        "- Validation globale 2021-05-05 -> 2026-05-05 : raw, silver, jours manquants, doublons, invalid rows, timestamps, partitions, available_ts, quarantines et stabilite schema.",
        "",
        "## Limites avant features/ML",
        "- Aucun feature store, dataset, ML, walk-forward, backtest, strategie ou signal avant validation V9.32 puis decision gate.",
        "",
        "## Garde-fous",
        "- Aucun trading, aucun paper live, aucun ordre, aucun backtest execute, aucun walk-forward, aucun ML, aucun dataset supervise.",
        "- Aucune strategie, aucun signal actionnable, aucun modele persistant, aucune API privee, aucune cle API.",
        "- Aucun telechargement de nouvelles donnees, aucune nouvelle ingestion, aucune suppression destructive, aucun push.",
        "- Aucun sidecar et aucune empreinte ZIP.",
    ]
    return "\n".join(lines) + "\n"


def update_state_surfaces_v9_30(root: Path, report: dict[str, Any]) -> None:
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "source_version": SOURCE_VERSION,
        "direction": DIRECTION,
        "v9_30_decision": report["decision"],
        "recommended_next_step": report["next_recommendation"],
        "validated_window_start": report["validated_window_start"],
        "validated_window_end": report["validated_window_end"],
        "target_5y_window_start": report["target_5y_window_start"],
        "target_5y_window_end": report["target_5y_window_end"],
        "extension_window_start": report["extension_window_start"],
        "extension_window_end": report["extension_window_end"],
        "extension_days_needed": report["extension_days_needed"],
        "estimated_extension_rows": report["estimated_extension_rows"],
        "estimated_extension_raw_bytes": report["estimated_extension_raw_bytes"],
        "estimated_extension_silver_bytes": report["estimated_extension_silver_bytes"],
        "safe_for_5y_extension_collection": report["safe_for_5y_extension_collection"],
        "storage_warning_level": report["storage_warning_level"],
        "features_created": False,
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "network_used": False,
        "new_data_downloaded": False,
        "ingestion_executed": False,
        **report["safety_flags"],
    }
    state_path = root / "reports/PROJECT_STATE.json"
    state = _read_json(state_path) if state_path.exists() else {}
    state.update(metrics)
    _write_json(state_path, state)
    _write_json(root / "reports/current/latest_metrics.json", metrics)
    text = (
        "# Synthese courante - V9.30\n\n"
        f"- Derniere version validee : `{LAST_VALIDATED_VERSION}`.\n"
        f"- Candidate : `{VERSION}`.\n"
        "- Statut : `pending_external_audit`.\n"
        f"- Direction : `{DIRECTION}`.\n"
        f"- Decision V9.30 : `{report['decision']}`.\n"
        f"- Fenetre validee : `{report['validated_window_start']}` -> `{report['validated_window_end']}`.\n"
        f"- Extension 5Y a collecter : `{report['extension_window_start']}` -> `{report['extension_window_end']}` (`{report['extension_days_needed']}` jours).\n"
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
        f"- Candidate : {VERSION}, plan d'extension historique aggTrades 5Y.\n"
        f"- Fenetre validee : {report['validated_window_start']} -> {report['validated_window_end']}.\n"
        f"- Extension planifiee : {report['extension_window_start']} -> {report['extension_window_end']}.\n"
        "- Aucun trading, ordre, backtest, walk-forward, strategie, signal actionnable, modele persistant, API privee ou cle API.\n"
        "- Aucun telechargement de nouvelles donnees, aucune ingestion, aucune suppression destructive, aucun sidecar et aucune empreinte ZIP.\n",
    )


def date_range_v9_30(start: str, end: str) -> list[str]:
    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    if end_date < start_date:
        raise ValueError("end date must be >= start date")
    return [(start_date + timedelta(days=offset)).isoformat() for offset in range((end_date - start_date).days + 1)]


def statvfs_free_v9_30(path: Path) -> dict[str, Any]:
    stat = os.statvfs(path)
    free = stat.f_bavail * stat.f_frsize
    return {"path": path.as_posix(), "free_bytes": free, "free_gib": round(free / 1024**3, 3)}


def run_local_command_v9_30(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    return {"command": command, "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}


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
