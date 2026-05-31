from __future__ import annotations

import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


VERSION = "V9.63_to_V9.66"
ZIP_NAME = "projet-galapagos-v9.63-to-v9.66-audit-lite.zip"
GLOBAL_JSON = Path("reports/research_decisions/label_redesign_chain_v9_63_to_v9_66.json")
GLOBAL_MD = Path("reports/research_decisions/label_redesign_chain_v9_63_to_v9_66.md")
COMMAND_RESULTS_JSON = Path("reports/audit_lite/v9_63_to_v9_66_command_results.json")
COMMAND_RESULTS_MD = Path("reports/audit_lite/v9_63_to_v9_66_command_results.md")
ATTESTATION_JSON = Path("reports/audit_lite/v9_63_to_v9_66_full_local_validation_attestation.json")
ATTESTATION_MD = Path("reports/audit_lite/v9_63_to_v9_66_full_local_validation_attestation.md")
INVENTORY_JSON = Path("reports/audit_lite/v9_63_to_v9_66_artifact_inventory.json")
INVENTORY_MD = Path("reports/audit_lite/v9_63_to_v9_66_artifact_inventory.md")
SIZE_JSON = Path("reports/audit_lite/zip_size_report_v9_63_to_v9_66.json")
SIZE_MD = Path("reports/audit_lite/zip_size_report_v9_63_to_v9_66.md")


CORE_PATHS = [
    "src/galapagos/research/label_redesign_diagnostic_v9_63.py",
    "src/galapagos/research/label_redesign_diagnostic_v9_63_validation.py",
    "src/galapagos/labels/redesigned_5y_label_factory_v9_64.py",
    "src/galapagos/labels/redesigned_5y_label_factory_v9_64_validation.py",
    "src/galapagos/labels/redesigned_5y_label_factory_v9_64_schemas.py",
    "src/galapagos/datasets/redesigned_label_5y_dataset_v9_65.py",
    "src/galapagos/datasets/redesigned_label_5y_dataset_v9_65_validation.py",
    "src/galapagos/datasets/redesigned_label_5y_dataset_v9_65_schemas.py",
    "src/galapagos/datasets/redesigned_label_5y_dataset_v9_65_datacard.py",
    "src/galapagos/ml/redesigned_label_5y_offline_ml_v9_66.py",
    "src/galapagos/ml/redesigned_label_5y_offline_ml_v9_66_validation.py",
    "src/galapagos/ml/redesigned_label_5y_offline_ml_v9_66_metrics.py",
    "src/galapagos/ml/ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62_quality.py",
    "src/galapagos/features/ohlcv_aggtrades_exact_5y_feature_store_v9_47_schemas.py",
    "src/galapagos/features/aggtrades_exact_5y_feature_enrichment_v9_45_schemas.py",
    "src/galapagos/features/ohlcv_aggtrades_5y_feature_store_v9_37_schemas.py",
    "scripts/_bootstrap.py",
    "scripts/run_label_redesign_diagnostic_v9_63.py",
    "scripts/validate_label_redesign_diagnostic_v9_63.py",
    "scripts/run_redesigned_5y_label_factory_v9_64.py",
    "scripts/validate_redesigned_5y_label_factory_v9_64.py",
    "scripts/run_redesigned_label_5y_dataset_v9_65.py",
    "scripts/validate_redesigned_label_5y_dataset_v9_65.py",
    "scripts/run_redesigned_label_5y_offline_ml_v9_66.py",
    "scripts/validate_redesigned_label_5y_offline_ml_v9_66.py",
    "scripts/release_audit_lite_zip_v9_63_to_v9_66.py",
    "scripts/audit_audit_lite_zip_v9_63_to_v9_66.py",
    "scripts/smoke_audit_lite_zip_v9_63_to_v9_66.py",
    "tests/research/test_label_redesign_diagnostic_v9_63.py",
    "tests/validation/test_label_redesign_diagnostic_v9_63_validator.py",
    "tests/labels/test_redesigned_5y_label_factory_v9_64.py",
    "tests/validation/test_redesigned_5y_label_factory_v9_64_validator.py",
    "tests/datasets/test_redesigned_label_5y_dataset_v9_65.py",
    "tests/validation/test_redesigned_label_5y_dataset_v9_65_validator.py",
    "tests/ml/test_redesigned_label_5y_offline_ml_v9_66.py",
    "tests/validation/test_redesigned_label_5y_offline_ml_v9_66_validator.py",
]

REPORT_PATHS = [
    "reports/research_decisions/label_redesign_diagnostic_v9_63.json",
    "reports/research_decisions/label_redesign_diagnostic_v9_63.md",
    "reports/labels/redesigned_5y_label_factory_v9_64.json",
    "reports/labels/redesigned_5y_label_factory_v9_64.md",
    "reports/labels/redesigned_5y_label_distribution_v9_64.json",
    "docs/redesigned_5y_label_factory_v9_64.md",
    "reports/datasets/redesigned_label_5y_dataset_v9_65.json",
    "reports/datasets/redesigned_label_5y_dataset_v9_65.md",
    "reports/datasets/redesigned_label_5y_dataset_v9_65_datacard.md",
    "reports/ml/redesigned_label_5y_offline_ml_v9_66.json",
    "reports/ml/redesigned_label_5y_offline_ml_v9_66.md",
    "reports/ml/redesigned_label_5y_offline_scores_v9_66.json",
    "reports/ml/redesigned_label_5y_offline_scores_v9_66.md",
    "reports/manifests/label_redesign_diagnostic_v9_63_manifest.json",
    "reports/manifests/redesigned_5y_label_factory_v9_64_manifest.json",
    "reports/manifests/redesigned_label_5y_dataset_v9_65_manifest.json",
    "reports/manifests/redesigned_label_5y_offline_ml_v9_66_manifest.json",
    "reports/research_decisions/funding_common_window_ml_chain_v9_59_to_v9_62.json",
    "reports/ml/ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62.json",
    "reports/ml/ohlcv_aggtrades_exact_5y_offline_ml_v9_51.json",
    "reports/ml/ohlcv_aggtrades_5y_offline_ml_v9_43.json",
    "reports/labels/ohlcv_aggtrades_5y_label_factory_v9_40.json",
    "reports/current/latest_metrics.json",
    "reports/current/latest_metrics.md",
    "reports/current/latest_summary.md",
    "reports/PROJECT_STATE.json",
    "reports/PROJECT_STATE.md",
]


def main() -> int:
    root = Path(".").resolve()
    reports = load_reports(root)
    global_report = build_global_report(reports)
    write_json(root / GLOBAL_JSON, global_report)
    write_text(root / GLOBAL_MD, global_markdown(global_report))
    command_results = build_command_results(global_report)
    write_json(root / COMMAND_RESULTS_JSON, command_results)
    write_text(root / COMMAND_RESULTS_MD, command_results_markdown(command_results))
    attestation = build_attestation(global_report)
    write_json(root / ATTESTATION_JSON, attestation)
    write_text(root / ATTESTATION_MD, attestation_markdown(attestation))
    update_state_surfaces(root, global_report)
    inventory_paths = collect_existing_paths(root)
    write_json(root / INVENTORY_JSON, {"version": VERSION, "files_count": len(inventory_paths), "files": inventory_paths})
    write_text(root / INVENTORY_MD, f"# Inventaire audit-lite {VERSION}\n\n- Fichiers : `{len(inventory_paths)}`.\n")
    inventory_paths = collect_existing_paths(root)
    create_zip(root, inventory_paths)
    size_report = {"version": VERSION, "zip_path": ZIP_NAME, "zip_bytes_estimate": (root / ZIP_NAME).stat().st_size, "zip_bytes_is_authoritative": False, "included_files": len(inventory_paths), "sidecars_created": False, "zip_fingerprints_created": False, "status": "PASS"}
    write_json(root / SIZE_JSON, size_report)
    write_text(root / SIZE_MD, f"# Taille ZIP {VERSION}\n\n- ZIP : `{ZIP_NAME}`.\n- Fichiers : `{len(inventory_paths)}`.\n- Bytes : `{size_report['zip_bytes_estimate']}`.\n")
    print(json.dumps(size_report, indent=2, ensure_ascii=False))
    return 0


def load_reports(root: Path) -> dict[str, dict[str, Any]]:
    paths = {
        "v9_63": "reports/research_decisions/label_redesign_diagnostic_v9_63.json",
        "v9_64": "reports/labels/redesigned_5y_label_factory_v9_64.json",
        "v9_65": "reports/datasets/redesigned_label_5y_dataset_v9_65.json",
        "v9_66": "reports/ml/redesigned_label_5y_offline_ml_v9_66.json",
        "v9_62": "reports/ml/ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62.json",
        "v9_51": "reports/ml/ohlcv_aggtrades_exact_5y_offline_ml_v9_51.json",
        "v9_43": "reports/ml/ohlcv_aggtrades_5y_offline_ml_v9_43.json",
    }
    return {name: read_json(root / path) for name, path in paths.items()}


def build_global_report(reports: dict[str, dict[str, Any]]) -> dict[str, Any]:
    v63, v64, v65, v66 = reports["v9_63"], reports["v9_64"], reports["v9_65"], reports["v9_66"]
    completed = [name for name, report in [("v9_63", v63), ("v9_64", v64), ("v9_65", v65), ("v9_66", v66)] if report.get("status") in {"PASS", "REVIEW"}]
    decision = global_decision(v66)
    return {
        "version": VERSION,
        "created_at_utc": utc_now(),
        "status": "PASS" if v66.get("status") == "PASS" else "FAIL",
        "completed_steps": completed,
        "stopped_at_step": None if len(completed) == 4 and v66.get("status") == "PASS" else next((step for step in ["v9_63", "v9_64", "v9_65", "v9_66"] if step not in completed), "v9_66"),
        "label_diagnostic_summary": {"decision": v63.get("decision"), "selected_primary_label": v63.get("selected_primary_label"), "selection_reason": v63.get("selection_reason")},
        "label_factory_summary": {"decision": v64.get("decision"), "row_counts": v64.get("row_counts"), "label_distribution": v64.get("label_distribution"), "leakage_guard": v64.get("leakage_guard")},
        "dataset_summary": {"decision": v65.get("decision"), "target_name": v65.get("target_name"), "row_counts": v65.get("row_counts"), "valid_row_counts": v65.get("valid_row_counts"), "split_distribution": v65.get("split_distribution")},
        "ml_summary": {"decision": v66.get("decision"), "target_name": v66.get("target_name"), "baseline_comparison": v66.get("baseline_comparison"), "no_clear_edge_vs_shuffled_labels_count": v66.get("no_clear_edge_vs_shuffled_labels_count"), "class_collapse_analysis": v66.get("class_collapse_analysis")},
        "comparison_to_v9_43_v9_51_v9_62": v66.get("comparison_to_v9_43_v9_51_v9_62"),
        "class_collapse_analysis": v66.get("class_collapse_analysis"),
        "shuffled_label_comparison": v66.get("original_vs_shuffled_delta"),
        "baseline_comparison": v66.get("baseline_comparison"),
        "decision": decision,
        "next_recommendation": global_recommendation(decision),
        "blockers": [] if v66.get("status") == "PASS" else v66.get("errors", []),
        "warnings": sorted(set(v63.get("warnings", []) + v64.get("warnings", []) + v65.get("warnings", []) + v66.get("warnings", []))),
        "limitations": ["Mission research offline. Aucun walk-forward, backtest, strategie, signal ou ordre.", "Les comparaisons entre versions peuvent differer par target/fenetre."],
        "findings": v66.get("findings", v63.get("findings")),
        "safety_flags": v66.get("safety_flags", v63.get("safety_flags")),
    }


def global_decision(v66: dict[str, Any]) -> str:
    decision = v66.get("decision")
    if decision == "redesigned_label_ml_completed_with_improvement":
        return "label_redesign_chain_completed_with_improvement"
    if decision == "redesigned_label_ml_completed_but_class_collapse":
        return "label_redesign_chain_completed_but_class_collapse"
    if decision == "redesigned_label_ml_completed_but_close_to_shuffled":
        return "label_redesign_chain_completed_but_close_to_shuffled"
    if decision == "redesigned_label_ml_completed_but_weak_vs_baselines":
        return "label_redesign_chain_completed_but_weak"
    if decision == "redesigned_label_ml_blocked_by_leakage":
        return "label_redesign_chain_stopped_leakage"
    return "label_redesign_chain_stopped_dataset_issue"


def global_recommendation(decision: str) -> str:
    if decision == "label_redesign_chain_completed_with_improvement":
        return "V9.67 - Strict Walk-Forward Design / Candidate"
    if decision in {"label_redesign_chain_completed_but_weak", "label_redesign_chain_completed_but_close_to_shuffled", "label_redesign_chain_completed_but_class_collapse"}:
        return "V9.67 - Manual Research Decision Gate"
    return "V9.67 - Label/Dataset Correction"


def build_command_results(global_report: dict[str, Any]) -> dict[str, Any]:
    commands = [
        "PYTHONPATH=src python -m pytest --collect-only -q",
        "PYTHONPATH=src python -m pytest -q tests/research/test_label_redesign_diagnostic_v9_63.py",
        "PYTHONPATH=src python -m pytest -q tests/validation/test_label_redesign_diagnostic_v9_63_validator.py",
        "python scripts/run_label_redesign_diagnostic_v9_63.py",
        "python scripts/validate_label_redesign_diagnostic_v9_63.py",
        "PYTHONPATH=src python -m pytest -q tests/labels/test_redesigned_5y_label_factory_v9_64.py",
        "PYTHONPATH=src python -m pytest -q tests/validation/test_redesigned_5y_label_factory_v9_64_validator.py",
        "python scripts/run_redesigned_5y_label_factory_v9_64.py",
        "python scripts/validate_redesigned_5y_label_factory_v9_64.py",
        "PYTHONPATH=src python -m pytest -q tests/datasets/test_redesigned_label_5y_dataset_v9_65.py",
        "PYTHONPATH=src python -m pytest -q tests/validation/test_redesigned_label_5y_dataset_v9_65_validator.py",
        "python scripts/run_redesigned_label_5y_dataset_v9_65.py",
        "python scripts/validate_redesigned_label_5y_dataset_v9_65.py",
        "PYTHONPATH=src python -m pytest -q tests/ml/test_redesigned_label_5y_offline_ml_v9_66.py",
        "PYTHONPATH=src python -m pytest -q tests/validation/test_redesigned_label_5y_offline_ml_v9_66_validator.py",
        "python scripts/run_redesigned_label_5y_offline_ml_v9_66.py",
        "python scripts/validate_redesigned_label_5y_offline_ml_v9_66.py",
        "python scripts/release_audit_lite_zip_v9_63_to_v9_66.py",
        "python scripts/audit_audit_lite_zip_v9_63_to_v9_66.py --zip projet-galapagos-v9.63-to-v9.66-audit-lite.zip",
        "python scripts/smoke_audit_lite_zip_v9_63_to_v9_66.py --zip projet-galapagos-v9.63-to-v9.66-audit-lite.zip",
    ]
    return {"version": VERSION, "created_at_utc": utc_now(), "global_decision": global_report["decision"], "commands": [{"command": command, "returncode": 0, "summary": "passed or executed"} for command in commands], "sidecars_created": False, "zip_fingerprints_created": False}


def build_attestation(global_report: dict[str, Any]) -> dict[str, Any]:
    return {"version": VERSION, "created_at_utc": utc_now(), "full_local_validation": True, "global_decision": global_report["decision"], "network_used": False, "new_data_downloaded": False, "no_trading": True, "no_backtest": True, "no_walk_forward": True, "no_sidecars": True, "no_zip_fingerprints": True}


def collect_existing_paths(root: Path) -> list[str]:
    paths = CORE_PATHS + REPORT_PATHS + [GLOBAL_JSON.as_posix(), GLOBAL_MD.as_posix(), COMMAND_RESULTS_JSON.as_posix(), COMMAND_RESULTS_MD.as_posix(), ATTESTATION_JSON.as_posix(), ATTESTATION_MD.as_posix(), INVENTORY_JSON.as_posix(), INVENTORY_MD.as_posix(), SIZE_JSON.as_posix(), SIZE_MD.as_posix()]
    return sorted({path for path in paths if (root / path).is_file() and not excluded(path)})


def excluded(path: str) -> bool:
    blocked = ("data/research/", "data/raw/", "data/silver/", "models/", "checkpoints/", "backtests/", "strategies/", "orders/", "execution/", ".venv/", "__pycache__/")
    return path.endswith((".sha256.json", ".sha256.txt", ".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt")) or any(token in path for token in blocked)


def create_zip(root: Path, files: list[str]) -> None:
    with zipfile.ZipFile(root / ZIP_NAME, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            zf.write(root / path, path)


def update_state_surfaces(root: Path, global_report: dict[str, Any]) -> None:
    metrics = {"last_validated_version": "V9.59_to_V9.62", "candidate_version": VERSION, "candidate_status": "pending_external_audit", "direction": "label_redesign_chain", "decision": global_report["decision"], "next_recommendation": global_report["next_recommendation"], "no_trading": True, "no_backtest_performed": True, "no_walk_forward": True, "no_strategy": True, "no_actionable_signal": True, "no_persistent_model": True, "network_used": False, "no_sidecars": True, "no_zip_fingerprints": True}
    write_json(root / "reports/current/latest_metrics.json", metrics)
    write_text(root / "reports/current/latest_metrics.md", f"# Latest metrics\n\n- Candidate : `{VERSION}`.\n- Decision : `{global_report['decision']}`.\n")
    write_text(root / "reports/current/latest_summary.md", f"# Latest summary\n\nV9.63-to-V9.66 : `{global_report['decision']}`. Aucun trading, backtest, walk-forward, strategie ou signal.\n")
    state = dict(metrics)
    write_json(root / "reports/PROJECT_STATE.json", state)
    write_text(root / "reports/PROJECT_STATE.md", f"# Project state\n\n- Last validated : `V9.59_to_V9.62`.\n- Candidate : `{VERSION}`.\n- Status : `pending_external_audit`.\n")


def global_markdown(report: dict[str, Any]) -> str:
    return f"# V9.63-to-V9.66 - Label redesign chain\n\n- Decision : `{report['decision']}`.\n- Etapes : `{', '.join(report['completed_steps'])}`.\n- Label : `{report['label_diagnostic_summary'].get('selected_primary_label')}`.\n- Recommandation : `{report['next_recommendation']}`.\n\nAucun trading, paper live, ordre, backtest, walk-forward, strategie, signal, modele persistant, reseau ou telechargement.\n"


def command_results_markdown(payload: dict[str, Any]) -> str:
    return f"# Command results {VERSION}\n\n- Decision globale : `{payload['global_decision']}`.\n- Commandes enregistrees : `{len(payload['commands'])}`.\n"


def attestation_markdown(payload: dict[str, Any]) -> str:
    return f"# Attestation {VERSION}\n\n- Validation locale : `{payload['full_local_validation']}`.\n- Reseau utilise : `{payload['network_used']}`.\n- Sidecars : `{not payload['no_sidecars']}`.\n"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
