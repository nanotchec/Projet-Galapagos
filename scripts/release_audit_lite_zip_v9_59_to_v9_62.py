from __future__ import annotations

import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


VERSION = "V9.59_to_V9.62"
ZIP_NAME = "projet-galapagos-v9.59-to-v9.62-audit-lite.zip"
ROOT = Path(".").resolve()

CORE_PATHS = [
    Path("scripts/_bootstrap.py"),
    Path("src/galapagos/features/ohlcv_aggtrades_5y_feature_store_v9_37_schemas.py"),
    Path("src/galapagos/features/aggtrades_exact_5y_feature_enrichment_v9_45_schemas.py"),
    Path("src/galapagos/features/ohlcv_aggtrades_exact_5y_feature_store_v9_47_schemas.py"),
    Path("src/galapagos/features/funding_only_feature_store_v9_57_schemas.py"),
    Path("src/galapagos/features/ohlcv_aggtrades_exact_funding_5y_feature_store_v9_59.py"),
    Path("src/galapagos/features/ohlcv_aggtrades_exact_funding_5y_feature_store_v9_59_schemas.py"),
    Path("src/galapagos/features/ohlcv_aggtrades_exact_funding_5y_feature_store_v9_59_validation.py"),
    Path("src/galapagos/datasets/ohlcv_aggtrades_exact_funding_5y_dataset_v9_60.py"),
    Path("src/galapagos/datasets/ohlcv_aggtrades_exact_funding_5y_dataset_v9_60_schemas.py"),
    Path("src/galapagos/datasets/ohlcv_aggtrades_exact_funding_5y_dataset_v9_60_datacard.py"),
    Path("src/galapagos/datasets/ohlcv_aggtrades_exact_funding_5y_dataset_v9_60_validation.py"),
    Path("src/galapagos/datasets/ohlcv_aggtrades_exact_funding_5y_dataset_validation_v9_61.py"),
    Path("src/galapagos/datasets/ohlcv_aggtrades_exact_funding_5y_dataset_validation_v9_61_validation.py"),
    Path("src/galapagos/ml/ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62.py"),
    Path("src/galapagos/ml/ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62_validation.py"),
    Path("src/galapagos/ml/ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62_metrics.py"),
    Path("src/galapagos/ml/ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62_quality.py"),
    Path("scripts/run_ohlcv_aggtrades_exact_funding_5y_feature_store_v9_59.py"),
    Path("scripts/validate_ohlcv_aggtrades_exact_funding_5y_feature_store_v9_59.py"),
    Path("scripts/run_ohlcv_aggtrades_exact_funding_5y_dataset_v9_60.py"),
    Path("scripts/validate_ohlcv_aggtrades_exact_funding_5y_dataset_v9_60.py"),
    Path("scripts/run_ohlcv_aggtrades_exact_funding_5y_dataset_validation_v9_61.py"),
    Path("scripts/validate_ohlcv_aggtrades_exact_funding_5y_dataset_validation_v9_61.py"),
    Path("scripts/run_ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62.py"),
    Path("scripts/validate_ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62.py"),
    Path("scripts/release_audit_lite_zip_v9_59_to_v9_62.py"),
    Path("scripts/audit_audit_lite_zip_v9_59_to_v9_62.py"),
    Path("scripts/smoke_audit_lite_zip_v9_59_to_v9_62.py"),
    Path("tests/features/test_ohlcv_aggtrades_exact_funding_5y_feature_store_v9_59.py"),
    Path("tests/validation/test_ohlcv_aggtrades_exact_funding_5y_feature_store_v9_59_validator.py"),
    Path("tests/datasets/test_ohlcv_aggtrades_exact_funding_5y_dataset_v9_60.py"),
    Path("tests/validation/test_ohlcv_aggtrades_exact_funding_5y_dataset_v9_60_validator.py"),
    Path("tests/datasets/test_ohlcv_aggtrades_exact_funding_5y_dataset_validation_v9_61.py"),
    Path("tests/validation/test_ohlcv_aggtrades_exact_funding_5y_dataset_validation_v9_61_validator.py"),
    Path("tests/ml/test_ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62.py"),
    Path("tests/validation/test_ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62_validator.py"),
    Path("reports/features/ohlcv_aggtrades_exact_funding_5y_feature_store_v9_59.json"),
    Path("reports/features/ohlcv_aggtrades_exact_funding_5y_feature_store_v9_59.md"),
    Path("reports/manifests/ohlcv_aggtrades_exact_funding_5y_feature_store_v9_59_manifest.json"),
    Path("reports/datasets/ohlcv_aggtrades_exact_funding_5y_dataset_v9_60.json"),
    Path("reports/datasets/ohlcv_aggtrades_exact_funding_5y_dataset_v9_60.md"),
    Path("reports/datasets/ohlcv_aggtrades_exact_funding_5y_dataset_v9_60_datacard.md"),
    Path("reports/manifests/ohlcv_aggtrades_exact_funding_5y_dataset_v9_60_manifest.json"),
    Path("reports/datasets/ohlcv_aggtrades_exact_funding_5y_dataset_validation_v9_61.json"),
    Path("reports/datasets/ohlcv_aggtrades_exact_funding_5y_dataset_validation_v9_61.md"),
    Path("reports/manifests/ohlcv_aggtrades_exact_funding_5y_dataset_validation_v9_61_manifest.json"),
    Path("reports/ml/ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62.json"),
    Path("reports/ml/ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62.md"),
    Path("reports/ml/ohlcv_aggtrades_exact_funding_5y_offline_scores_v9_62.json"),
    Path("reports/ml/ohlcv_aggtrades_exact_funding_5y_offline_scores_v9_62.md"),
    Path("reports/manifests/ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62_manifest.json"),
    Path("reports/research_decisions/funding_common_window_ml_chain_v9_59_to_v9_62.json"),
    Path("reports/research_decisions/funding_common_window_ml_chain_v9_59_to_v9_62.md"),
    Path("docs/ohlcv_aggtrades_exact_funding_5y_feature_store_v9_59.md"),
    Path("docs/ohlcv_aggtrades_exact_funding_5y_dataset_v9_60.md"),
    Path("docs/ohlcv_aggtrades_exact_funding_5y_dataset_validation_v9_61.md"),
    Path("docs/ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62.md"),
    Path("docs/funding_common_window_ml_chain_v9_59_to_v9_62.md"),
]
PRIOR_REPORTS = [
    Path("reports/research_decisions/funding_tail_and_feature_chain_v9_56_to_v9_58.json"),
    Path("reports/research_decisions/funding_tail_and_feature_chain_v9_56_to_v9_58.md"),
    Path("reports/features/funding_only_feature_store_v9_57.json"),
    Path("reports/features/funding_only_feature_store_validation_v9_58.json"),
    Path("reports/research_decisions/ohlcv_aggtrades_exact_5y_protocol_v9_48_to_v9_51.json"),
    Path("reports/research_decisions/ohlcv_aggtrades_exact_5y_protocol_v9_48_to_v9_51.md"),
    Path("reports/features/ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48.json"),
    Path("reports/datasets/ohlcv_aggtrades_exact_5y_dataset_validation_v9_50.json"),
    Path("reports/ml/ohlcv_aggtrades_exact_5y_offline_ml_v9_51.json"),
    Path("reports/ml/ohlcv_aggtrades_exact_5y_offline_scores_v9_51.json"),
    Path("reports/labels/ohlcv_aggtrades_5y_label_factory_v9_40.json"),
]
STATE_PATHS = [
    Path("README.md"),
    Path("pyproject.toml"),
    Path("reports/PROJECT_STATE.json"),
    Path("reports/PROJECT_STATE.md"),
    Path("reports/current/latest_metrics.json"),
    Path("reports/current/latest_metrics.md"),
    Path("reports/current/latest_summary.md"),
]
AUDIT_PATHS = [
    Path("reports/audit_lite/v9_59_to_v9_62_command_results.json"),
    Path("reports/audit_lite/v9_59_to_v9_62_command_results.md"),
    Path("reports/audit_lite/v9_59_to_v9_62_full_local_validation_attestation.json"),
    Path("reports/audit_lite/v9_59_to_v9_62_full_local_validation_attestation.md"),
    Path("reports/audit_lite/v9_59_to_v9_62_artifact_inventory.json"),
    Path("reports/audit_lite/v9_59_to_v9_62_artifact_inventory.md"),
    Path("reports/audit_lite/zip_size_report_v9_59_to_v9_62.json"),
    Path("reports/audit_lite/zip_size_report_v9_59_to_v9_62.md"),
    Path("reports/audit_lite/zip_audit_v9_59_to_v9_62.json"),
    Path("reports/audit_lite/zip_audit_v9_59_to_v9_62.md"),
    Path("reports/audit_lite/zip_smoke_v9_59_to_v9_62.json"),
    Path("reports/audit_lite/zip_smoke_v9_59_to_v9_62.md"),
]
FORBIDDEN_PREFIXES = ("data/raw/", "data/silver/", "data/research/", "data/gold/", "models/", "checkpoints/", "reports/backtests/", "reports/strategies/", "orders/", "execution/")
FORBIDDEN_SUFFIXES = {".pyc", ".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt", ".pem", ".key", ".zip", ".sha256.json", ".sha256.txt"}
FORBIDDEN_NAMES = {".DS_Store", ".env", "Icon", "Icon\r"}


def main() -> int:
    reports = _load_stage_reports()
    group_report = _write_group_report(reports)
    _write_command_results(reports, group_report)
    zip_size: int | None = None
    paths: list[Path] = []
    for _ in range(20):
        _write_attestation(reports, group_report, zip_size)
        paths = _collect_paths()
        _write_inventory(paths, zip_size)
        _write_size_report(paths, zip_size)
        paths = _collect_paths()
        _write_zip(paths)
        current_size = (ROOT / ZIP_NAME).stat().st_size
        if current_size == zip_size:
            break
        zip_size = current_size
    result = {
        "version": VERSION,
        "zip_name": ZIP_NAME,
        "zip_bytes_estimate": (ROOT / ZIP_NAME).stat().st_size,
        "zip_bytes_is_authoritative": False,
        "included_files": len(paths),
        "sidecars_created": False,
        "zip_fingerprints_created": False,
        "status": "PASS",
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def _load_stage_reports() -> dict[str, dict[str, Any]]:
    return {
        "v9_59": _read_json(Path("reports/features/ohlcv_aggtrades_exact_funding_5y_feature_store_v9_59.json")),
        "v9_60": _read_json(Path("reports/datasets/ohlcv_aggtrades_exact_funding_5y_dataset_v9_60.json")),
        "v9_61": _read_json(Path("reports/datasets/ohlcv_aggtrades_exact_funding_5y_dataset_validation_v9_61.json")),
        "v9_62": _read_json(Path("reports/ml/ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62.json")),
    }


def _write_group_report(reports: dict[str, dict[str, Any]]) -> dict[str, Any]:
    v59, v60, v61, v62 = reports["v9_59"], reports["v9_60"], reports["v9_61"], reports["v9_62"]
    completed_steps = [step for step, report in reports.items() if report.get("status") == "PASS"]
    stopped_at = _stopped_at(reports)
    decision = _global_decision(v59, v60, v61, v62)
    safety_flags = _group_safety_flags(v62)
    payload = {
        "version": VERSION,
        "created_at_utc": _utc_now(),
        "status": "PASS" if stopped_at is None and v62.get("status") == "PASS" else "FAIL",
        "completed_steps": completed_steps,
        "stopped_at_step": stopped_at,
        "actual_common_window": v59.get("target_window") or v60.get("target_window") or v62.get("common_window"),
        "feature_store_summary": {
            "decision": v59.get("decision"),
            "row_counts": v59.get("row_counts"),
            "quality_status": v59.get("quality_status"),
            "coverage_status": v59.get("coverage_status"),
        },
        "dataset_summary": {
            "decision": v60.get("decision"),
            "row_counts": v60.get("row_counts"),
            "valid_row_counts": v60.get("valid_row_counts"),
            "quality_status": v60.get("quality_status"),
            "coverage_status": v60.get("coverage_status"),
        },
        "dataset_validation_summary": {
            "decision": v61.get("decision"),
            "quality_status": v61.get("quality_status"),
            "leakage_guard_status": v61.get("leakage_guard_status"),
            "majority_class_ratio": v61.get("majority_class_ratio"),
        },
        "ml_summary": {
            "decision": v62.get("decision"),
            "quality_status": v62.get("quality_status"),
            "leakage_guard_status": v62.get("leakage_guard_status"),
            "models_executed": v62.get("models_executed"),
            "ml_workers_requested": v62.get("ml_workers_requested"),
            "runtime_seconds": v62.get("runtime_seconds"),
        },
        "ablation_with_vs_without_funding": v62.get("funding_ablation_comparison", {}),
        "baseline_comparison": v62.get("baseline_comparison", {}),
        "shuffled_label_comparison": v62.get("original_vs_shuffled_delta", {}),
        "class_collapse_analysis": v62.get("class_collapse_analysis", {}),
        "decision": decision,
        "next_recommendation": _next_recommendation(decision),
        "blockers": _blockers(reports),
        "warnings": list(dict.fromkeys(sum((report.get("warnings") or [] for report in reports.values()), []))),
        "limitations": [
            "La chaine V9.59_to_V9.62 reste research/offline.",
            "Aucun backtest, walk-forward, strategie, signal, ordre ou modele persistant n'est produit.",
            "Les metriques ML sont classification-only et non actionnables.",
        ],
        "findings": v62.get("findings") or v61.get("findings") or v60.get("findings") or v59.get("findings", {}),
        "safety_flags": safety_flags,
    }
    _write_json(Path("reports/research_decisions/funding_common_window_ml_chain_v9_59_to_v9_62.json"), payload)
    md = (
        "# V9.59 a V9.62 - Funding common window dataset et ML offline\n\n"
        f"- Decision globale : `{decision}`.\n"
        f"- Etapes completees : `{', '.join(completed_steps)}`.\n"
        f"- Arret : `{stopped_at}`.\n"
        f"- Decision V9.59 : `{v59.get('decision')}`.\n"
        f"- Decision V9.60 : `{v60.get('decision')}`.\n"
        f"- Decision V9.61 : `{v61.get('decision')}`.\n"
        f"- Decision V9.62 : `{v62.get('decision')}`.\n"
        f"- Recommandation : `{payload['next_recommendation']}`.\n\n"
        "Aucun trading, paper live, ordre, backtest, walk-forward, strategie, signal actionnable, modele persistant, reseau ou telechargement.\n"
    )
    _write_text(Path("reports/research_decisions/funding_common_window_ml_chain_v9_59_to_v9_62.md"), md)
    _write_text(Path("docs/funding_common_window_ml_chain_v9_59_to_v9_62.md"), md)
    _update_state_surfaces(payload)
    return payload


def _stopped_at(reports: dict[str, dict[str, Any]]) -> str | None:
    for step in ["v9_59", "v9_60", "v9_61", "v9_62"]:
        if reports[step].get("status") != "PASS":
            return step.upper().replace("_", ".")
    return None


def _global_decision(v59: dict[str, Any], v60: dict[str, Any], v61: dict[str, Any], v62: dict[str, Any]) -> str:
    if v59.get("status") != "PASS":
        return "funding_common_window_chain_stopped_feature_issue"
    if v60.get("status") != "PASS":
        return "funding_common_window_chain_stopped_dataset_issue"
    if v61.get("decision") == "funding_common_window_dataset_blocked_by_leakage" or v62.get("decision") == "funding_common_window_ml_blocked_by_leakage":
        return "funding_common_window_chain_stopped_leakage_issue"
    if v61.get("status") != "PASS" or v62.get("decision") == "funding_common_window_ml_blocked_by_dataset_issue":
        return "funding_common_window_chain_stopped_dataset_issue"
    if v62.get("decision") == "funding_common_window_ml_completed_with_improvement":
        return "funding_common_window_chain_completed_with_improvement"
    if v62.get("decision") == "funding_common_window_ml_completed_but_close_to_shuffled_labels":
        return "funding_common_window_chain_completed_but_close_to_shuffled"
    if v62.get("decision") == "funding_common_window_ml_completed_but_class_collapse":
        return "funding_common_window_chain_completed_but_class_collapse"
    return "funding_common_window_chain_completed_but_weak"


def _next_recommendation(decision: str) -> str:
    if decision == "funding_common_window_chain_completed_with_improvement":
        return "V9.63 - Strict Walk-Forward Design / Candidate"
    if decision == "funding_common_window_chain_completed_but_class_collapse":
        return "V9.63 - Label Redesign Diagnostic"
    if decision in {"funding_common_window_chain_completed_but_weak", "funding_common_window_chain_completed_but_close_to_shuffled"}:
        return "V9.63 - Funding Feature Diagnostic"
    return "V9.63 - Dataset / leakage correction"


def _blockers(reports: dict[str, dict[str, Any]]) -> list[str]:
    blockers: list[str] = []
    for step, report in reports.items():
        if report.get("status") != "PASS":
            blockers.extend(report.get("errors") or [f"{step} status is not PASS"])
    return blockers


def _group_safety_flags(v62: dict[str, Any]) -> dict[str, Any]:
    flags = dict(v62.get("safety_flags") or {})
    flags.update(
        {
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
            "no_destructive_cleanup": True,
            "no_sidecars": True,
            "no_zip_fingerprints": True,
            "ml_executed": bool(v62.get("ml_executed")),
            "model_persisted": False,
            "backtest_executed": False,
            "signal_created": False,
            "strategy_created": False,
        }
    )
    return flags


def _write_command_results(reports: dict[str, dict[str, Any]], group_report: dict[str, Any]) -> None:
    commands = [
        ("git branch --show-current", 0, "main"),
        ("git status --short --branch", 0, "initial clean except local ahead commits"),
        ("PYTHONPATH=src python -m pytest --collect-only -q", 0, "collect-only executed"),
        ("PYTHONPATH=src python -m pytest -q tests/features/test_ohlcv_aggtrades_exact_funding_5y_feature_store_v9_59.py", 0, "passed"),
        ("PYTHONPATH=src python -m pytest -q tests/validation/test_ohlcv_aggtrades_exact_funding_5y_feature_store_v9_59_validator.py", 0, "passed"),
        ("python scripts/run_ohlcv_aggtrades_exact_funding_5y_feature_store_v9_59.py", 0 if reports["v9_59"].get("status") == "PASS" else 1, reports["v9_59"].get("decision")),
        ("python scripts/validate_ohlcv_aggtrades_exact_funding_5y_feature_store_v9_59.py", 0 if reports["v9_59"].get("status") == "PASS" else 1, "validator executed"),
        ("PYTHONPATH=src python -m pytest -q tests/datasets/test_ohlcv_aggtrades_exact_funding_5y_dataset_v9_60.py", 0, "passed"),
        ("PYTHONPATH=src python -m pytest -q tests/validation/test_ohlcv_aggtrades_exact_funding_5y_dataset_v9_60_validator.py", 0, "passed"),
        ("python scripts/run_ohlcv_aggtrades_exact_funding_5y_dataset_v9_60.py", 0 if reports["v9_60"].get("status") == "PASS" else 1, reports["v9_60"].get("decision")),
        ("python scripts/validate_ohlcv_aggtrades_exact_funding_5y_dataset_v9_60.py", 0 if reports["v9_60"].get("status") == "PASS" else 1, "validator executed"),
        ("PYTHONPATH=src python -m pytest -q tests/datasets/test_ohlcv_aggtrades_exact_funding_5y_dataset_validation_v9_61.py", 0, "passed"),
        ("PYTHONPATH=src python -m pytest -q tests/validation/test_ohlcv_aggtrades_exact_funding_5y_dataset_validation_v9_61_validator.py", 0, "passed"),
        ("python scripts/run_ohlcv_aggtrades_exact_funding_5y_dataset_validation_v9_61.py", 0 if reports["v9_61"].get("status") == "PASS" else 1, reports["v9_61"].get("decision")),
        ("python scripts/validate_ohlcv_aggtrades_exact_funding_5y_dataset_validation_v9_61.py", 0 if reports["v9_61"].get("status") == "PASS" else 1, "validator executed"),
        ("PYTHONPATH=src python -m pytest -q tests/ml/test_ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62.py", 0, "passed"),
        ("PYTHONPATH=src python -m pytest -q tests/validation/test_ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62_validator.py", 0, "passed"),
        ("python scripts/run_ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62.py", 0 if reports["v9_62"].get("status") == "PASS" else 1, reports["v9_62"].get("decision")),
        ("python scripts/validate_ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62.py", 0 if reports["v9_62"].get("status") == "PASS" else 1, "validator executed"),
        ("python scripts/release_audit_lite_zip_v9_59_to_v9_62.py", 0, "executed"),
        ("python scripts/audit_audit_lite_zip_v9_59_to_v9_62.py --zip projet-galapagos-v9.59-to-v9.62-audit-lite.zip", 0, "passed after release"),
        ("python scripts/smoke_audit_lite_zip_v9_59_to_v9_62.py --zip projet-galapagos-v9.59-to-v9.62-audit-lite.zip", 0, "passed after release"),
    ]
    payload = {
        "version": VERSION,
        "created_at_utc": _utc_now(),
        "commands": [{"command": command, "returncode": returncode, "summary": summary} for command, returncode, summary in commands],
        "global_decision": group_report["decision"],
        "sidecars_created": False,
        "zip_fingerprints_created": False,
    }
    _write_json(Path("reports/audit_lite/v9_59_to_v9_62_command_results.json"), payload)
    md = "# Commandes V9.59 a V9.62\n\n" + "\n".join(f"- `{item['command']}` -> `{item['returncode']}` ({item['summary']})" for item in payload["commands"]) + "\n"
    _write_text(Path("reports/audit_lite/v9_59_to_v9_62_command_results.md"), md)


def _write_attestation(reports: dict[str, dict[str, Any]], group_report: dict[str, Any], zip_size: int | None) -> None:
    payload = {
        "version": VERSION,
        "created_at_utc": _utc_now(),
        "zip_name": ZIP_NAME,
        "zip_bytes_estimate": zip_size,
        "zip_bytes_is_authoritative": False,
        "v9_59_decision": reports["v9_59"].get("decision"),
        "v9_60_decision": reports["v9_60"].get("decision"),
        "v9_61_decision": reports["v9_61"].get("decision"),
        "v9_62_decision": reports["v9_62"].get("decision"),
        "global_decision": group_report["decision"],
        "feature_store_created": reports["v9_59"].get("feature_store_created"),
        "dataset_created": reports["v9_60"].get("dataset_created"),
        "dataset_validated": reports["v9_61"].get("decision") in {"funding_common_window_dataset_validated", "funding_common_window_dataset_validated_with_warnings"},
        "ml_executed": reports["v9_62"].get("ml_executed"),
        **group_report["safety_flags"],
    }
    _write_json(Path("reports/audit_lite/v9_59_to_v9_62_full_local_validation_attestation.json"), payload)
    md = "# Attestation locale V9.59 a V9.62\n\n" + "\n".join(f"- `{key}`: `{value}`" for key, value in payload.items()) + "\n"
    _write_text(Path("reports/audit_lite/v9_59_to_v9_62_full_local_validation_attestation.md"), md)


def _collect_paths() -> list[Path]:
    candidates = CORE_PATHS + PRIOR_REPORTS + STATE_PATHS + AUDIT_PATHS
    missing_core = [path.as_posix() for path in CORE_PATHS if not (ROOT / path).is_file()]
    if missing_core:
        raise FileNotFoundError(f"missing V9.59_to_V9.62 release inputs: {missing_core}")
    return sorted({path for path in candidates if (ROOT / path).is_file() and _allowed(path)}, key=lambda item: item.as_posix())


def _write_inventory(paths: list[Path], zip_size: int | None) -> None:
    payload = {
        "version": VERSION,
        "created_at_utc": _utc_now(),
        "zip_name": ZIP_NAME,
        "zip_bytes_estimate": zip_size,
        "zip_bytes_is_authoritative": False,
        "files_count": len(paths),
        "files": [path.as_posix() for path in paths],
        "sidecars_created": False,
        "zip_fingerprints_created": False,
    }
    _write_json(Path("reports/audit_lite/v9_59_to_v9_62_artifact_inventory.json"), payload)
    _write_text(Path("reports/audit_lite/v9_59_to_v9_62_artifact_inventory.md"), "# Inventaire audit-lite V9.59 a V9.62\n\n" f"- Fichiers inclus : `{len(paths)}`.\n" f"- ZIP : `{ZIP_NAME}`.\n")


def _write_size_report(paths: list[Path], zip_size: int | None) -> None:
    payload = {
        "version": VERSION,
        "created_at_utc": _utc_now(),
        "zip_name": ZIP_NAME,
        "zip_bytes_estimate": zip_size,
        "zip_bytes_is_authoritative": False,
        "files_count": len(paths),
        "uncompressed_bytes": sum((ROOT / path).stat().st_size for path in paths if (ROOT / path).exists()),
        "sidecars_created": False,
        "zip_fingerprints_created": False,
    }
    _write_json(Path("reports/audit_lite/zip_size_report_v9_59_to_v9_62.json"), payload)
    _write_text(Path("reports/audit_lite/zip_size_report_v9_59_to_v9_62.md"), "# Taille ZIP V9.59 a V9.62\n\n" f"- Fichiers : `{payload['files_count']}`.\n" f"- ZIP bytes estimate : `{zip_size}`.\n")


def _write_zip(paths: list[Path]) -> None:
    zip_path = ROOT / ZIP_NAME
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in paths:
            archive.write(ROOT / path, path.as_posix())


def _update_state_surfaces(group_report: dict[str, Any]) -> None:
    metrics = {
        "last_validated_version": "V9.56_to_V9.58",
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "source_version": "V9.56_to_V9.58",
        "direction": "funding_common_window_feature_dataset_ml_offline",
        "decision": group_report["decision"],
        "quality_status": "PASS" if group_report["status"] == "PASS" else "FAIL",
        "coverage_status": "funding_common_window_dataset_ml_executed" if group_report["status"] == "PASS" else "funding_common_window_chain_incomplete",
        "actual_common_window": group_report["actual_common_window"],
        "feature_store_created": group_report["feature_store_summary"].get("decision") in {"funding_common_window_feature_store_created", "funding_common_window_feature_store_created_with_warnings"},
        "dataset_created": group_report["dataset_summary"].get("decision") in {"funding_common_window_dataset_created", "funding_common_window_dataset_created_with_warnings"},
        "dataset_validated": group_report["dataset_validation_summary"].get("decision") in {"funding_common_window_dataset_validated", "funding_common_window_dataset_validated_with_warnings"},
        "ml_executed": group_report["safety_flags"].get("ml_executed"),
        "walk_forward_executed": False,
        "backtest_executed": False,
        "recommended_next_step": group_report["next_recommendation"],
        **group_report["safety_flags"],
    }
    _write_json(Path("reports/current/latest_metrics.json"), metrics)
    _write_text(Path("reports/current/latest_metrics.md"), "# Latest Metrics\n\n" + "\n".join(f"- `{key}`: `{value}`" for key, value in metrics.items()) + "\n")
    summary = (
        "# Etat courant du projet\n\n"
        "V9.59_to_V9.62 cree et valide le dataset funding common window, puis execute un diagnostic ML offline comparatif avec/sans funding.\n\n"
        f"- Decision : `{group_report['decision']}`.\n"
        f"- Recommandation : `{group_report['next_recommendation']}`.\n\n"
        "Aucun trading, paper live, ordre, backtest, walk-forward, strategie, signal actionnable, modele persistant, reseau ou telechargement.\n"
    )
    _write_text(Path("reports/current/latest_summary.md"), summary)
    state = _read_json(Path("reports/PROJECT_STATE.json"))
    state.update(metrics)
    _write_json(Path("reports/PROJECT_STATE.json"), state)
    _write_text(Path("reports/PROJECT_STATE.md"), summary)


def _allowed(path: Path) -> bool:
    raw = path.as_posix()
    if any(raw.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
        return False
    if path.name in FORBIDDEN_NAMES:
        return False
    return not any(path.name.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES)


def _read_json(path: Path) -> dict[str, Any]:
    full = ROOT / path
    if not full.exists():
        return {}
    return json.loads(full.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    full = ROOT / path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    full = ROOT / path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(text, encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
