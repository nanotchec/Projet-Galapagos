from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from galapagos.data.aggtrades_post_v9_collection_v9_18 import (
    FINDINGS,
    FUNDING_FIRST_END,
    FUNDING_FIRST_START,
    MARKET_TYPE,
    PUBLIC_ARCHIVE_HOST,
    RAW_DIR,
    SILVER_PARTITION_TEMPLATE,
    SYMBOL,
    TARGET_END,
    TARGET_START,
    TRADE_SOURCE_TYPE,
    VENUE,
    raw_zip_path_for_date_v9_18,
    silver_path_for_date_v9_18,
)


VERSION = "V9.22"
SOURCE_VERSION = "V9.21"
LAST_VALIDATED_VERSION = "V9.21"
TARGET_WINDOW_START = FUNDING_FIRST_START
TARGET_WINDOW_END = FUNDING_FIRST_END
CURRENT_EXPECTED_COVERAGE_START = "2024-05-05"
CURRENT_EXPECTED_COVERAGE_END = "2024-08-09"
NEXT_REMAINING_START = "2024-08-10"
PLANNED_BATCH_DAYS = 60
DIRECTION = "aggtrades_post_v9_multi_batch_completion_plan"

REPORT_JSON_PATH = Path("reports/data/aggtrades_post_v9_multi_batch_plan_v9_22.json")
REPORT_MD_PATH = Path("reports/data/aggtrades_post_v9_multi_batch_plan_v9_22.md")
MANIFEST_PATH = Path("reports/manifests/aggtrades_post_v9_multi_batch_plan_v9_22_manifest.json")
DOC_PATH = Path("docs/aggtrades_post_v9_multi_batch_plan_v9_22.md")

INPUT_PATHS = {
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

ALLOWED_DECISIONS = {
    "multi_batch_completion_plan_ready",
    "multi_batch_completion_plan_ready_with_disk_warning",
    "multi_batch_completion_plan_not_ready_need_coverage_repair",
    "multi_batch_completion_plan_not_ready_need_storage_review",
    "stop_aggtrades_completion_branch",
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
    "network_used": False,
    "no_new_data_download": True,
    "no_ingestion_executed": True,
    "no_sidecars": True,
    "no_zip_fingerprints": True,
}


def run_aggtrades_post_v9_multi_batch_plan_v9_22(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report = build_aggtrades_post_v9_multi_batch_plan_v9_22(root)
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_22(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / MANIFEST_PATH, build_manifest_v9_22(report))
    update_state_surfaces_v9_22(root, report)
    return report


def build_aggtrades_post_v9_multi_batch_plan_v9_22(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    current_coverage = build_current_coverage_v9_22(root)
    cumulative_metrics = build_cumulative_metrics_v9_22(inputs)
    remaining_window = build_remaining_window_v9_22(current_coverage)
    estimated_remaining = estimate_remaining_volume_v9_22(remaining_window, cumulative_metrics)
    proposed_batches = build_proposed_batches_v9_22(remaining_window, cumulative_metrics)
    storage_warning = build_storage_warning_v9_22(estimated_remaining, proposed_batches)
    decision = decide_v9_22(current_coverage, proposed_batches, storage_warning)
    report = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": "PASS",
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "mode": "plan-only",
        "inputs_used": {name: {"path": item["path"], "available": item["available"]} for name, item in inputs.items()},
        "source_public_target": build_source_design_v9_22(),
        "current_coverage": current_coverage,
        "remaining_window": remaining_window,
        "cumulative_metrics": cumulative_metrics,
        "estimated_remaining_volume": estimated_remaining,
        "proposed_batches": proposed_batches,
        "checkpoint_policy": build_checkpoint_policy_v9_22(),
        "quality_policy": build_quality_policy_v9_22(),
        "rollback_policy": build_rollback_policy_v9_22(),
        "storage_warning": storage_warning,
        "v9_22_decision": decision,
        "next_recommendation": decision["next_recommendation"],
        "collection_executed": False,
        "network_used": False,
        "new_data_downloaded": False,
        "ingestion_executed": False,
        "features_created": False,
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "complete_collection_reached": False,
        "blockers": decision["blockers"],
        "warnings": build_warnings_v9_22(current_coverage, storage_warning),
        "limitations": [
            "V9.22 est un plan de completion multi-batch; aucune collecte, aucun telechargement et aucune ingestion ne sont executes.",
            "Les estimations de volume et de runtime sont derivees des batches V9.19, V9.20 et V9.21 deja valides.",
            "La future couverture complete funding-first reste a executer par versions separees et auditees.",
        ],
        "findings": dict(FINDINGS),
        "safety_flags": dict(BASE_SAFETY_FLAGS),
    }
    return report


def build_source_design_v9_22() -> dict[str, Any]:
    return {
        "source_name": "Binance public archive aggTrades daily files",
        "host": PUBLIC_ARCHIVE_HOST,
        "venue": VENUE,
        "market_type": MARKET_TYPE,
        "symbol": SYMBOL,
        "trade_source_type": TRADE_SOURCE_TYPE,
        "target_window_start": TARGET_WINDOW_START,
        "target_window_end": TARGET_WINDOW_END,
        "global_post_v9_window_start": TARGET_START,
        "global_post_v9_window_end": TARGET_END,
        "account_required": False,
        "api_key_required": False,
        "private_endpoint_required": False,
        "exchange_auth_required": False,
        "websocket_live_required": False,
        "v9_22_network_used": False,
        "raw_pattern": (RAW_DIR / "BTCUSDT-aggTrades-YYYY-MM-DD.zip").as_posix(),
        "silver_pattern": SILVER_PARTITION_TEMPLATE,
    }


def build_current_coverage_v9_22(root: Path) -> dict[str, Any]:
    target_dates = date_range_v9_22(TARGET_WINDOW_START, TARGET_WINDOW_END)
    expected_current_dates = date_range_v9_22(CURRENT_EXPECTED_COVERAGE_START, CURRENT_EXPECTED_COVERAGE_END)
    complete_dates: list[str] = []
    missing_expected: list[str] = []
    raw_missing: list[str] = []
    silver_missing: list[str] = []
    for day_value in expected_current_dates:
        raw_path = root / raw_zip_path_for_date_v9_18(day_value)
        silver_path = root / silver_path_for_date_v9_18(day_value)
        raw_ok = raw_path.exists() and raw_path.stat().st_size > 0
        silver_ok = silver_path.exists() and silver_path.stat().st_size > 0
        if raw_ok and silver_ok:
            complete_dates.append(day_value)
        else:
            missing_expected.append(day_value)
            if not raw_ok:
                raw_missing.append(day_value)
            if not silver_ok:
                silver_missing.append(day_value)
    contiguous_dates: list[str] = []
    for day_value in expected_current_dates:
        if day_value not in complete_dates:
            break
        contiguous_dates.append(day_value)
    gaps = [day_value for day_value in expected_current_dates if day_value not in complete_dates]
    current_start = contiguous_dates[0] if contiguous_dates else None
    current_end = contiguous_dates[-1] if contiguous_dates else None
    remaining_days = len(target_dates) - len(contiguous_dates)
    return {
        "target_window_start": TARGET_WINDOW_START,
        "target_window_end": TARGET_WINDOW_END,
        "current_coverage_start": current_start,
        "current_coverage_end": current_end,
        "expected_current_coverage_start": CURRENT_EXPECTED_COVERAGE_START,
        "expected_current_coverage_end": CURRENT_EXPECTED_COVERAGE_END,
        "days_covered": len(contiguous_dates),
        "days_remaining": remaining_days,
        "target_days_total": len(target_dates),
        "gaps_detected": gaps,
        "raw_missing_dates": raw_missing,
        "silver_missing_dates": silver_missing,
        "v9_19_days": 7,
        "v9_20_days": 30,
        "v9_21_days": 60,
        "current_coverage_is_continuous": not gaps and len(contiguous_dates) == len(expected_current_dates),
        "complete_dates_sample": {
            "first": complete_dates[:3],
            "last": complete_dates[-3:],
        },
        "local_metadata_only": True,
    }


def build_remaining_window_v9_22(current_coverage: dict[str, Any]) -> dict[str, Any]:
    if current_coverage["current_coverage_end"]:
        start = (date.fromisoformat(current_coverage["current_coverage_end"]) + timedelta(days=1)).isoformat()
    else:
        start = TARGET_WINDOW_START
    end = TARGET_WINDOW_END
    dates = date_range_v9_22(start, end) if date.fromisoformat(start) <= date.fromisoformat(end) else []
    return {
        "remaining_start": start if dates else None,
        "remaining_end": end if dates else None,
        "remaining_days": len(dates),
        "target_completion_end": TARGET_WINDOW_END,
        "complete_target_coverage_reached": len(dates) == 0,
    }


def build_cumulative_metrics_v9_22(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    batches = [
        _extract_batch_metrics("V9.19", inputs["v9_19_pilot_collection"]["payload"]),
        _extract_batch_metrics("V9.20", inputs["v9_20_batch_collection"]["payload"]),
        _extract_batch_metrics("V9.21", inputs["v9_21_batch_expansion"]["payload"]),
    ]
    total_days = sum(item["days_complete"] for item in batches)
    total_rows = sum(item["total_rows"] for item in batches)
    raw_bytes = sum(item["raw_bytes_total"] for item in batches)
    silver_bytes = sum(item["silver_bytes_total"] for item in batches)
    runtime_seconds = sum(item["runtime_seconds"] for item in batches)
    return {
        "reported_batches": batches,
        "days_collected_total": total_days,
        "raw_bytes_collected_total": raw_bytes,
        "silver_bytes_collected_total": silver_bytes,
        "rows_collected_total": total_rows,
        "runtime_seconds_total": round(runtime_seconds, 3),
        "average_rows_per_day": int(total_rows / total_days) if total_days else 0,
        "average_raw_bytes_per_day": int(raw_bytes / total_days) if total_days else 0,
        "average_silver_bytes_per_day": int(silver_bytes / total_days) if total_days else 0,
        "average_runtime_seconds_per_day": round(runtime_seconds / total_days, 3) if total_days else 0,
    }


def estimate_remaining_volume_v9_22(remaining_window: dict[str, Any], cumulative_metrics: dict[str, Any]) -> dict[str, Any]:
    days = int(remaining_window["remaining_days"])
    return {
        "days_remaining": days,
        "estimated_remaining_rows": cumulative_metrics["average_rows_per_day"] * days,
        "estimated_remaining_raw_bytes": cumulative_metrics["average_raw_bytes_per_day"] * days,
        "estimated_remaining_silver_bytes": cumulative_metrics["average_silver_bytes_per_day"] * days,
        "estimated_remaining_runtime_seconds": round(cumulative_metrics["average_runtime_seconds_per_day"] * days, 3),
        "estimate_source": "V9.19+V9.20+V9.21 realized averages",
        "zip_bytes_is_authoritative": False,
    }


def build_proposed_batches_v9_22(remaining_window: dict[str, Any], cumulative_metrics: dict[str, Any]) -> list[dict[str, Any]]:
    if not remaining_window["remaining_start"] or not remaining_window["remaining_end"]:
        return []
    remaining_dates = date_range_v9_22(remaining_window["remaining_start"], remaining_window["remaining_end"])
    batches: list[dict[str, Any]] = []
    for index, offset in enumerate(range(0, len(remaining_dates), PLANNED_BATCH_DAYS), start=1):
        chunk = remaining_dates[offset : offset + PLANNED_BATCH_DAYS]
        days = len(chunk)
        cumulative_end = chunk[-1]
        batch_total_bytes = (cumulative_metrics["average_raw_bytes_per_day"] + cumulative_metrics["average_silver_bytes_per_day"]) * days
        batches.append(
            {
                "batch_id": f"V9.23_batch_{index:02d}",
                "start_date": chunk[0],
                "end_date": chunk[-1],
                "max_downloads": days,
                "expected_days": days,
                "estimated_raw_bytes": cumulative_metrics["average_raw_bytes_per_day"] * days,
                "estimated_silver_bytes": cumulative_metrics["average_silver_bytes_per_day"] * days,
                "estimated_rows": cumulative_metrics["average_rows_per_day"] * days,
                "estimated_runtime_seconds": round(cumulative_metrics["average_runtime_seconds_per_day"] * days, 3),
                "expected_cumulative_coverage_end": cumulative_end,
                "checkpoint_required": True,
                "audit_required_after_batch": True,
                "disk_warning_level": disk_warning_level_v9_22(batch_total_bytes),
                "recommendation_status": "priority_batch" if index == 1 else "planned_followup_batch",
            }
        )
    return batches


def build_checkpoint_policy_v9_22() -> dict[str, Any]:
    return {
        "batch_size_days": PLANNED_BATCH_DAYS,
        "max_single_version_days": PLANNED_BATCH_DAYS,
        "external_audit_after_each_batch": True,
        "global_coverage_validation_after_final_batch": True,
        "do_not_collect_full_remaining_window_in_one_version": True,
        "next_batch_recommended": {
            "start_date": NEXT_REMAINING_START,
            "end_date": "2024-10-08",
            "max_downloads": 60,
        },
        "stop_conditions": [
            "any day_failed or day_quarantined",
            "disk free space below review threshold",
            "raw/silver size sanity check fails",
            "duplicate aggregate_trade_id appears within a day",
            "timestamp or available_ts checks fail",
        ],
    }


def build_quality_policy_v9_22() -> dict[str, Any]:
    return {
        "daily_quality_checks": [
            "raw ZIP present and non-empty",
            "archive readable with one CSV payload",
            "normalized silver Parquet present and non-empty",
            "price and quantity strictly positive",
            "UTC timestamps and date partition alignment",
            "available_ts >= event_ts",
            "no duplicate aggregate_trade_id within a day",
            "row_valid and invalid_reason audited",
        ],
        "cumulative_quality_checks": [
            "continuous date coverage from target start to latest completed day",
            "duplicate checks across adjacent days",
            "aggregate_trade_id continuity warnings across adjacent days",
            "timestamp continuity and gap warnings across adjacent days",
            "raw/silver size sanity checks by day and by batch",
            "manifest per batch plus global coverage manifest",
        ],
        "forbidden_actions": [
            "no labels",
            "no supervised dataset",
            "no ML",
            "no walk-forward",
            "no backtest",
            "no strategy",
            "no actionable signal",
        ],
    }


def build_rollback_policy_v9_22() -> dict[str, Any]:
    return {
        "skip_days_already_complete": True,
        "never_overwrite_complete_raw_or_silver_without_explicit_repair_mode": True,
        "quarantine_partial_or_failed_days": True,
        "batch_failure_result": "do not mark cumulative coverage complete; repair or rerun failed days only",
        "retry_policy": {
            "retry_failed_public_downloads_only": True,
            "do_not_delete_successful_days": True,
            "resume_from_manifest_and_existing_day_status": True,
        },
        "rollback_plan": [
            "preserve complete days",
            "move partial raw files to quarantine",
            "remove or quarantine partial silver outputs for failed days",
            "rerun validate-only before any next batch",
        ],
    }


def build_storage_warning_v9_22(estimated_remaining: dict[str, Any], proposed_batches: list[dict[str, Any]]) -> dict[str, Any]:
    remaining_total = int(estimated_remaining["estimated_remaining_raw_bytes"] + estimated_remaining["estimated_remaining_silver_bytes"])
    level = "low"
    if remaining_total >= 25_000_000_000:
        level = "medium"
    if remaining_total >= 75_000_000_000:
        level = "high"
    return {
        "level": level,
        "storage_review_required_before_full_completion": level in {"medium", "high"},
        "remaining_raw_plus_silver_bytes_estimate": remaining_total,
        "largest_batch_raw_plus_silver_bytes_estimate": max(
            (int(batch["estimated_raw_bytes"] + batch["estimated_silver_bytes"]) for batch in proposed_batches),
            default=0,
        ),
        "guidance": "Verifier l'espace disque libre avant chaque batch; ne pas lancer plusieurs batches sans checkpoint audit.",
    }


def decide_v9_22(
    current_coverage: dict[str, Any],
    proposed_batches: list[dict[str, Any]],
    storage_warning: dict[str, Any],
) -> dict[str, Any]:
    if current_coverage["gaps_detected"]:
        decision = "multi_batch_completion_plan_not_ready_need_coverage_repair"
        recommendation = "V9.23 - AggTrades Coverage Repair."
        confidence = "high"
        blockers = ["current coverage has local raw/silver gaps"]
        justification = "La couverture actuelle n'est pas continue; reparer avant de planifier la suite."
    elif not proposed_batches and not current_coverage["days_remaining"]:
        decision = "multi_batch_completion_plan_ready"
        recommendation = "V9.23 - Funding-First Feature Window Readiness."
        confidence = "medium"
        blockers = []
        justification = "La fenetre cible est deja couverte localement."
    elif storage_warning["level"] == "high":
        decision = "multi_batch_completion_plan_not_ready_need_storage_review"
        recommendation = "V9.23 - Storage Review Before Full Collection."
        confidence = "medium"
        blockers = ["remaining estimated storage volume is high"]
        justification = "Le volume restant estime exige une revue stockage avant execution."
    elif storage_warning["level"] == "medium":
        decision = "multi_batch_completion_plan_ready_with_disk_warning"
        recommendation = "V9.23 - AggTrades Post-V9 Batch 2 Collection."
        confidence = "high"
        blockers = []
        justification = "La couverture actuelle est continue et le plan existe, mais le volume restant impose des checkpoints disque."
    else:
        decision = "multi_batch_completion_plan_ready"
        recommendation = "V9.23 - AggTrades Post-V9 Batch 2 Collection."
        confidence = "high"
        blockers = []
        justification = "La couverture actuelle est continue et le plan multi-batch est raisonnable."
    return {
        "decision": decision,
        "confidence": confidence,
        "justification": justification,
        "next_recommendation": recommendation,
        "blockers": blockers,
        "no_backtest": True,
        "no_walk_forward": True,
        "no_trading": True,
    }


def build_manifest_v9_22(report: dict[str, Any]) -> dict[str, Any]:
    coverage = report["current_coverage"]
    remaining = report["remaining_window"]
    estimates = report["estimated_remaining_volume"]
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": report["status"],
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "mode": report["mode"],
        "report_path": REPORT_JSON_PATH.as_posix(),
        "markdown_path": REPORT_MD_PATH.as_posix(),
        "target_window_start": coverage["target_window_start"],
        "target_window_end": coverage["target_window_end"],
        "current_coverage_start": coverage["current_coverage_start"],
        "current_coverage_end": coverage["current_coverage_end"],
        "days_covered": coverage["days_covered"],
        "days_remaining": coverage["days_remaining"],
        "gaps_detected": coverage["gaps_detected"],
        "remaining_start": remaining["remaining_start"],
        "remaining_end": remaining["remaining_end"],
        "proposed_batches_count": len(report["proposed_batches"]),
        "estimated_remaining_rows": estimates["estimated_remaining_rows"],
        "estimated_remaining_raw_bytes": estimates["estimated_remaining_raw_bytes"],
        "estimated_remaining_silver_bytes": estimates["estimated_remaining_silver_bytes"],
        "v9_22_decision": report["v9_22_decision"],
        "collection_executed": False,
        "network_used": False,
        "new_data_downloaded": False,
        "ingestion_executed": False,
        "findings": report["findings"],
        "safety_flags": report["safety_flags"],
    }


def build_markdown_v9_22(report: dict[str, Any]) -> str:
    coverage = report["current_coverage"]
    metrics = report["cumulative_metrics"]
    estimates = report["estimated_remaining_volume"]
    decision = report["v9_22_decision"]
    batches = report["proposed_batches"]
    lines = [
        "# V9.22 - AggTrades Post-V9 Multi-Batch Completion Plan",
        "",
        "## Resume executif",
        "- Version de planification uniquement : aucune collecte, aucun telechargement et aucune ingestion.",
        f"- Decision V9.22 : `{decision['decision']}`.",
        f"- Justification : {decision['justification']}",
        f"- Recommandation suivante : {decision['next_recommendation']}",
        "- Aucun label, dataset supervise, ML, walk-forward, backtest, strategie ou signal actionnable.",
        "",
        "## Couverture actuelle",
        f"- Fenetre cible funding-first : `{coverage['target_window_start']}` -> `{coverage['target_window_end']}`.",
        f"- Couverture courante : `{coverage['current_coverage_start']}` -> `{coverage['current_coverage_end']}`.",
        f"- Jours couverts : `{coverage['days_covered']}`.",
        f"- Jours restants : `{coverage['days_remaining']}`.",
        f"- Gaps detectes : `{coverage['gaps_detected']}`.",
        f"- Jours V9.19/V9.20/V9.21 : `{coverage['v9_19_days']}` / `{coverage['v9_20_days']}` / `{coverage['v9_21_days']}`.",
        "",
        "## Volumes",
        f"- Raw bytes deja collectes : `{metrics['raw_bytes_collected_total']}`.",
        f"- Silver bytes deja collectes : `{metrics['silver_bytes_collected_total']}`.",
        f"- Lignes deja collectees : `{metrics['rows_collected_total']}`.",
        f"- Moyenne lignes/jour : `{metrics['average_rows_per_day']}`.",
        f"- Moyenne raw bytes/jour : `{metrics['average_raw_bytes_per_day']}`.",
        f"- Moyenne silver bytes/jour : `{metrics['average_silver_bytes_per_day']}`.",
        f"- Lignes restantes estimees : `{estimates['estimated_remaining_rows']}`.",
        f"- Raw bytes restants estimes : `{estimates['estimated_remaining_raw_bytes']}`.",
        f"- Silver bytes restants estimes : `{estimates['estimated_remaining_silver_bytes']}`.",
        f"- Runtime restant estime secondes : `{estimates['estimated_remaining_runtime_seconds']}`.",
        "",
        "## Plan multi-batch",
        f"- Nombre de batches proposes : `{len(batches)}`.",
        f"- Taille standard : `{PLANNED_BATCH_DAYS}` jours maximum par batch.",
    ]
    for batch in batches:
        lines.append(
            f"- `{batch['batch_id']}` : `{batch['start_date']}` -> `{batch['end_date']}`, "
            f"`{batch['expected_days']}` jours, raw `{batch['estimated_raw_bytes']}`, "
            f"silver `{batch['estimated_silver_bytes']}`, statut `{batch['recommendation_status']}`."
        )
    lines.extend(
        [
            "",
            "## Reprise et qualite",
            "- Skip des jours deja complets.",
            "- Aucun overwrite raw/silver complet sans mode repair explicite.",
            "- Quarantine des jours partiels ou echoues.",
            "- Manifest par batch et validation globale de couverture apres dernier batch.",
            "- Checks quotidiens et cumules sur timestamps, tailles, doublons et continuite.",
            "",
            "## Stockage",
            f"- Niveau alerte disque : `{report['storage_warning']['level']}`.",
            f"- Revue stockage avant completion complete : `{report['storage_warning']['storage_review_required_before_full_completion']}`.",
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
            "- Aucun reseau.",
            "- Aucun telechargement de nouvelles donnees.",
            "- Aucune ingestion executee.",
            "- Aucun sidecar et aucune empreinte ZIP.",
        ]
    )
    return "\n".join(lines) + "\n"


def update_state_surfaces_v9_22(root: Path, report: dict[str, Any]) -> None:
    coverage = report["current_coverage"]
    metrics = report["cumulative_metrics"]
    estimates = report["estimated_remaining_volume"]
    state_metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "source_version": SOURCE_VERSION,
        "direction": DIRECTION,
        "mode": report["mode"],
        "v9_22_decision": report["v9_22_decision"]["decision"],
        "recommended_next_step": report["next_recommendation"],
        "target_window_start": coverage["target_window_start"],
        "target_window_end": coverage["target_window_end"],
        "current_coverage_start": coverage["current_coverage_start"],
        "current_coverage_end": coverage["current_coverage_end"],
        "days_covered": coverage["days_covered"],
        "days_remaining": coverage["days_remaining"],
        "gaps_detected": coverage["gaps_detected"],
        "raw_bytes_collected_total": metrics["raw_bytes_collected_total"],
        "silver_bytes_collected_total": metrics["silver_bytes_collected_total"],
        "rows_collected_total": metrics["rows_collected_total"],
        "estimated_remaining_rows": estimates["estimated_remaining_rows"],
        "estimated_remaining_raw_bytes": estimates["estimated_remaining_raw_bytes"],
        "estimated_remaining_silver_bytes": estimates["estimated_remaining_silver_bytes"],
        "proposed_batches_count": len(report["proposed_batches"]),
        "collection_executed": False,
        "complete_collection_reached": False,
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
    for stale_key in ["recommended_next_version", "recommended_next_action"]:
        state.pop(stale_key, None)
    state.update(state_metrics)
    _write_json(state_path, state)
    _write_json(root / "reports/current/latest_metrics.json", state_metrics)
    text = (
        "# Synthese courante - V9.22\n\n"
        "- Derniere version validee : `V9.21`.\n"
        "- Candidate : `V9.22`.\n"
        "- Statut : `pending_external_audit`.\n"
        "- Direction : plan de completion multi-batch aggTrades post-V9.\n"
        f"- Couverture actuelle : `{coverage['current_coverage_start']}` -> `{coverage['current_coverage_end']}`.\n"
        f"- Jours couverts/restants : `{coverage['days_covered']}` / `{coverage['days_remaining']}`.\n"
        f"- Gaps detectes : `{coverage['gaps_detected']}`.\n"
        f"- Decision V9.22 : `{report['v9_22_decision']['decision']}`.\n"
        f"- Recommandation : {report['next_recommendation']}\n"
        "- Aucun reseau, telechargement, ingestion, label, dataset supervise, ML, walk-forward, backtest, strategie ou signal actionnable.\n"
        "- Aucun trading, paper live, ordre, modele persistant, API privee, cle API, client exchange authentifie ou websocket live.\n"
        "- Aucun sidecar et aucune empreinte ZIP.\n"
    )
    _write_text(root / "reports/PROJECT_STATE.md", text)
    _write_text(root / "reports/current/latest_summary.md", text)
    _write_text(root / "reports/current/latest_metrics.md", text)
    _write_text(
        root / "README.md",
        "# Projet Galapagos\n\n"
        "- Derniere version validee : V9.21.\n"
        "- Candidate : V9.22, plan de completion multi-batch aggTrades post-V9.\n"
        "- Couverture actuelle : 2024-05-05 -> 2024-08-09.\n"
        "- Fenetre restante planifiee : 2024-08-10 -> 2026-05-05.\n"
        "- Aucun trading, ordre, backtest, walk-forward, strategie, signal actionnable, modele persistant, API privee ou cle API.\n"
        "- Aucun client exchange authentifie, aucun websocket live, aucun reseau, aucun telechargement, aucune ingestion, aucun sidecar et aucune empreinte ZIP.\n",
    )


def _extract_batch_metrics(version: str, payload: dict[str, Any]) -> dict[str, Any]:
    if "batch_validation" in payload:
        summary = payload["batch_validation"]["summary"]
    elif "pilot_validation" in payload:
        summary = payload["pilot_validation"]["summary"]
    else:
        summary = {}
    return {
        "version": version,
        "days_complete": int(summary.get("days_complete") or 0),
        "total_rows": int(summary.get("total_rows") or 0),
        "raw_bytes_total": int(summary.get("raw_bytes_total") or 0),
        "silver_bytes_total": int(summary.get("silver_bytes_total") or 0),
        "runtime_seconds": float(summary.get("runtime_seconds") or 0),
    }


def build_warnings_v9_22(current_coverage: dict[str, Any], storage_warning: dict[str, Any]) -> list[str]:
    warnings = [
        "V9.22 ne collecte aucun nouveau jour.",
        "La couverture complete funding-first reste partielle.",
    ]
    if current_coverage["gaps_detected"]:
        warnings.append("Des gaps locaux raw/silver existent dans la couverture deja revendiquee.")
    if storage_warning["level"] != "low":
        warnings.append("Le volume restant estime justifie une verification disque avant chaque batch.")
    return warnings


def disk_warning_level_v9_22(total_bytes: int) -> str:
    if total_bytes >= 8_000_000_000:
        return "high"
    if total_bytes >= 2_000_000_000:
        return "medium"
    return "low"


def date_range_v9_22(start: str, end: str) -> list[str]:
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
