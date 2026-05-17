from __future__ import annotations

import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
for path in (PROJECT_ROOT, SRC_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from galapagos.research.mini_research_dataset_readiness import (
    EXPECTED_APPROVAL_PHRASE,
    EXPECTED_FUTURE_SCOPE,
    MiniResearchDatasetPhysicalAuditor,
    build_anti_leakage_plan,
    design_dataset_seed,
    evaluate_approval_phrase,
    validate_payload,
    validate_report_set,
)

_SMOKE_SPEC = importlib.util.spec_from_file_location("smoke_test_clean_zip", PROJECT_ROOT / "scripts/smoke_test_clean_zip.py")
if _SMOKE_SPEC is None or _SMOKE_SPEC.loader is None:
    raise RuntimeError("smoke_test_clean_zip.py cannot be loaded")
_SMOKE = importlib.util.module_from_spec(_SMOKE_SPEC)
_SMOKE_SPEC.loader.exec_module(_SMOKE)


def _copy_data(root: Path) -> None:
    for rel in [
        "data/research/microstructure_contract_materialization/v1_84",
        "data/research/microstructure_contract_materialization/v1_87",
        "data/research/microstructure_contract_materialization/v1_90",
    ]:
        shutil.copytree(PROJECT_ROOT / rel, root / rel)


def _payload() -> dict:
    physical = MiniResearchDatasetPhysicalAuditor(PROJECT_ROOT).audit()
    return {
        "version": "V1.91",
        "final_verdict": "V1_91_POST_CONSOLIDATION_REVIEW_AND_DATASET_SEED_READINESS_PASSED",
        "post_consolidation_review_executed": True,
        "dataset_seed_design_executed": True,
        "approval_gate_only": True,
        "reports_only": True,
        "dataset_seed_created": False,
        "dataset_created": False,
        "data_contract_actual_write_executed": False,
        "materialization_executed": False,
        "new_materialization_executed": False,
        "scope_drift_detected": False,
        "data_directory_writes_allowed": False,
        "data_directory_write_attempted": False,
        "new_data_files_created": False,
        "existing_data_files_modified": False,
        "existing_v1_84_files_modified": False,
        "existing_v1_87_files_modified": False,
        "existing_v1_90_files_modified": False,
        "no_new_data_directory_writes": True,
        "research_dataset_updated": False,
        "physical_files_created_count": 0,
        "network_executed": False,
        "new_network_requests_executed": False,
        "request_retry_count": 0,
        "pagination_used": False,
        "authenticated_request_allowed": False,
        "secrets_used": False,
        "strategy_link_allowed": False,
        "trading_allowed": False,
        "no_strategy_validated": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "real_orders_possible": False,
        "holdout_executed": False,
        "codex_cli_called": False,
        "ml_signal_validation_executed": False,
        "predictions_created": False,
        "labels_created": False,
        "targets_created": False,
        "release_ready_for_external_review": True,
        "clean_zip_ready_for_external_review": True,
        "smoke_test_passed": True,
        "blocking_reason": None,
        **evaluate_approval_phrase(EXPECTED_APPROVAL_PHRASE),
        **physical,
        **design_dataset_seed(),
        **build_anti_leakage_plan(),
    }


def _write_json(root: Path, rel: str, payload: dict) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_md(root: Path, rel: str, text: str = "V1.91") -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_report_set(root: Path) -> None:
    _copy_data(root)
    summary = _payload()
    physical = MiniResearchDatasetPhysicalAuditor(root).audit()
    for rel, payload in {
        "reports/research/mini_research_dataset_readiness_summary_v1_91.json": summary,
        "reports/research/mini_research_dataset_readiness_physical_audit_v1_91.json": {"version": "V1.91", **physical},
        "reports/research/mini_research_dataset_seed_design_v1_91.json": {"version": "V1.91", **design_dataset_seed()},
        "reports/research/mini_research_dataset_anti_leakage_plan_v1_91.json": {"version": "V1.91", **build_anti_leakage_plan()},
        "reports/research/mini_research_dataset_approval_decision_v1_91.json": {"version": "V1.91", **evaluate_approval_phrase(EXPECTED_APPROVAL_PHRASE)},
        "reports/research/mini_research_dataset_readiness_safety_check_v1_91.json": {"version": "V1.91"},
        "reports/research/mini_research_dataset_readiness_consistency_check_v1_91.json": {"version": "V1.91"},
        "reports/current/latest_metrics.json": summary,
        "reports/PROJECT_STATE.json": summary,
        "reports/release_zip_v1_91.json": {"version": "V1.91", "release_ready_for_external_review": True, "clean_zip_ready_for_external_review": True},
        "reports/zip_audit_v1_91.json": {"version": "V1.91", "clean_zip_ready_for_external_review": True},
        "reports/zip_smoke_test_v1_91.json": {"version": "V1.91", "smoke_test_passed": True},
    }.items():
        _write_json(root, rel, payload)
        if rel.startswith("reports/research/"):
            _write_md(root, str(Path(rel).with_suffix(".md")))
    _write_md(root, "reports/REPORT_INDEX.md", "V1.91 v1_91")
    _write_md(root, "docs/code_review_v1_91.md")
    _write_md(root, "docs/mini_research_dataset_readiness_v1_91.md")


def _errors_with(field: str, value) -> list[str]:
    payload = _payload()
    payload[field] = value
    return validate_payload(payload)


def test_empty_approval_phrase_denies():
    decision = evaluate_approval_phrase("")
    assert decision["human_approval_granted"] is False
    assert decision["v1_92_authorized"] is False


def test_wrong_approval_phrase_denies():
    decision = evaluate_approval_phrase("wrong")
    assert decision["approval_phrase_match"] is False


def test_exact_approval_phrase_grants_future_v1_92_only():
    decision = evaluate_approval_phrase(EXPECTED_APPROVAL_PHRASE)
    assert decision["human_approval_granted"] is True
    assert decision["authorized_future_version"] == "V1.92"
    assert decision["authorized_future_scope"] == EXPECTED_FUTURE_SCOPE


def test_approval_does_not_execute_v1_92():
    assert evaluate_approval_phrase(EXPECTED_APPROVAL_PHRASE)["v1_92_execution_attempted"] is False


def test_approval_does_not_write_data():
    assert _payload()["data_directory_write_attempted"] is False


def test_physical_audit_reads_v1_84_v1_87_v1_90_only():
    audit = MiniResearchDatasetPhysicalAuditor(PROJECT_ROOT).audit()
    assert audit["v1_84_files_count"] == 3
    assert audit["v1_87_files_count"] == 2
    assert audit["v1_90_files_count"] == 3


def test_physical_audit_rejects_missing_v1_90_file(tmp_path):
    _copy_data(tmp_path)
    (tmp_path / "data/research/microstructure_contract_materialization/v1_90/consolidated_manifest.json").unlink()
    assert MiniResearchDatasetPhysicalAuditor(tmp_path).audit()["v1_90_files_count"] != 3


def test_physical_audit_rejects_extra_v1_90_file(tmp_path):
    _copy_data(tmp_path)
    _write_json(tmp_path, "data/research/microstructure_contract_materialization/v1_90/extra.json", {"extra": 1})
    assert MiniResearchDatasetPhysicalAuditor(tmp_path).audit()["v1_90_unexpected_files_count"] == 1


def test_physical_audit_rejects_v1_90_hash_mismatch(tmp_path):
    _write_report_set(tmp_path)
    (tmp_path / "data/research/microstructure_contract_materialization/v1_90/consolidated_manifest.json").write_text("{}", encoding="utf-8")
    assert validate_report_set(tmp_path)


def test_dataset_seed_plan_is_reports_only():
    assert design_dataset_seed()["dataset_seed_plan_reports_only"] is True


def test_dataset_seed_plan_has_bounded_future_root():
    assert design_dataset_seed()["future_dataset_seed_allowed_root"] == "data/research/dataset_seed/v1_92/"


def test_dataset_seed_plan_rejects_more_than_five_future_files():
    assert _errors_with("future_dataset_seed_max_files", 6)


def test_dataset_seed_plan_rejects_forbidden_future_extension():
    payload = _payload()
    payload["future_dataset_seed_allowed_extensions"] = [".json", ".csv"]
    assert validate_payload(payload)


def test_anti_leakage_plan_defines_available_ts_rule():
    assert build_anti_leakage_plan()["feature_available_ts_lte_decision_ts_rule_defined"] is True


def test_anti_leakage_plan_defines_no_lookahead_policy():
    assert build_anti_leakage_plan()["no_lookahead_policy_defined"] is True


def test_anti_leakage_plan_defines_provenance_policy():
    assert build_anti_leakage_plan()["provenance_policy_defined"] is True


def test_validator_rejects_data_write_attempted_true():
    assert _errors_with("data_directory_write_attempted", True)


def test_validator_rejects_new_data_files_created_true():
    assert _errors_with("new_data_files_created", True)


def test_validator_rejects_existing_data_files_modified_true():
    assert _errors_with("existing_data_files_modified", True)


def test_validator_rejects_network_executed_true():
    assert _errors_with("network_executed", True)


def test_validator_rejects_dataset_created_true():
    assert _errors_with("dataset_created", True)


def test_validator_rejects_trading_allowed_true():
    assert _errors_with("trading_allowed", True)


def test_validator_rejects_real_orders_possible_true():
    assert _errors_with("real_orders_possible", True)


def test_validator_rejects_ml_signal_validation_executed_true():
    assert _errors_with("ml_signal_validation_executed", True)


def test_validator_rejects_v1_92_execution_attempted_true():
    assert _errors_with("v1_92_execution_attempted", True)


def test_validator_rejects_approval_granted_with_phrase_mismatch():
    payload = _payload()
    payload["approval_phrase_match"] = False
    payload["human_approval_granted"] = True
    assert validate_payload(payload)


def test_validator_rejects_missing_available_ts_policy():
    assert _errors_with("available_ts_policy_defined", False)


def test_validator_rejects_future_dataset_seed_max_files_above_5():
    assert _errors_with("future_dataset_seed_max_files", 7)


def test_report_index_references_v1_91(tmp_path):
    _write_report_set(tmp_path)
    assert not validate_report_set(tmp_path)


def test_smoke_v1_91_runs_validator_import_and_summary_presence():
    commands = _SMOKE.get_commands_for_version("v1_91")
    assert commands[0][1] == "scripts/validate_mini_research_dataset_readiness_v1_91_reports.py"
    assert "import galapagos" in commands[1][2]
    assert "mini_research_dataset_readiness_summary_v1_91.json" in commands[2][2]


def test_cross_file_alignment_summary_latest_metrics_project_state(tmp_path):
    _write_report_set(tmp_path)
    latest = json.loads((tmp_path / "reports/current/latest_metrics.json").read_text(encoding="utf-8"))
    latest["network_executed"] = True
    _write_json(tmp_path, "reports/current/latest_metrics.json", latest)
    assert validate_report_set(tmp_path)


def test_no_pass_only_tests_in_v1_91():
    content = Path(__file__).read_text(encoding="utf-8")
    assert not re.search(r"^\s*pass\s*$", content, re.MULTILINE)


def test_no_assert_true_or_true_in_v1_91():
    content = Path(__file__).read_text(encoding="utf-8")
    assert ("assert " + "True") not in content
    assert ("or " + "True") not in content
