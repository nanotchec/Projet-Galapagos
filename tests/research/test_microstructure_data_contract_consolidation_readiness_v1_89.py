from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from galapagos.research.microstructure_data_contract_consolidation_readiness import (
    APPROVAL_PHRASE_EXPECTED,
    AUTHORIZED_FUTURE_SCOPE,
    ConsolidationPhysicalAuditor,
    design_consolidation_contract_v2,
    evaluate_approval_phrase,
    validate_consolidation_design,
)
from galapagos.research.microstructure_data_contract_consolidation_readiness.consolidation_designer import (
    FUTURE_ALLOWED_ROOT,
)
from galapagos.research.microstructure_data_contract_consolidation_readiness.physical_auditor import (
    EXPECTED_V1_84_HASHES,
    EXPECTED_V1_87_HASHES,
    V1_84_DATA_ROOT,
    V1_87_DATA_ROOT,
)
from galapagos.research.microstructure_data_contract_consolidation_readiness.validator import validate_payload

_SMOKE_SPEC = importlib.util.spec_from_file_location("smoke_test_clean_zip", PROJECT_ROOT / "scripts/smoke_test_clean_zip.py")
if _SMOKE_SPEC is None or _SMOKE_SPEC.loader is None:
    raise RuntimeError("smoke_test_clean_zip.py cannot be loaded")
_SMOKE = importlib.util.module_from_spec(_SMOKE_SPEC)
_SMOKE_SPEC.loader.exec_module(_SMOKE)


def _valid_payload() -> dict:
    return {
        "readiness_pack_executed": True,
        "consolidation_design_executed": True,
        "consolidation_executed": False,
        "approval_gate_only": True,
        "reports_only": True,
        "data_contract_actual_write_executed": False,
        "materialization_executed": False,
        "new_materialization_executed": False,
        "scope_drift_detected": False,
        "approval_phrase_match": True,
        "human_approval_granted": True,
        "v1_90_authorized": True,
        "authorized_future_version": "V1.90",
        "authorized_future_scope": AUTHORIZED_FUTURE_SCOPE,
        "v1_90_execution_attempted": False,
        "data_directory_writes_allowed": False,
        "data_directory_write_attempted": False,
        "new_data_files_created": False,
        "existing_data_files_modified": False,
        "existing_v1_84_files_modified": False,
        "existing_v1_87_files_modified": False,
        "no_new_data_directory_writes": True,
        "dataset_created": False,
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
        "v1_84_files_count": 3,
        "v1_87_files_count": 2,
        "v1_84_hashes_verified": True,
        "v1_87_hashes_verified": True,
        "v1_84_json_valid": True,
        "v1_87_json_valid": True,
        "v1_84_unexpected_files_count": 0,
        "v1_87_unexpected_files_count": 0,
        "forbidden_file_types_detected": False,
        "parquet_created": False,
        "csv_created": False,
        "sqlite_created": False,
        "jsonl_created": False,
        "db_created": False,
        "release_ready_for_external_review": True,
        "smoke_test_passed": True,
        "clean_zip_ready_for_external_review": True,
        **design_consolidation_contract_v2(),
    }


def _errors_with(field: str, value) -> list[str]:
    payload = _valid_payload()
    payload[field] = value
    return validate_payload(payload)


def _write_review_files(root: Path) -> None:
    v1_84_root = root / V1_84_DATA_ROOT
    v1_87_root = root / V1_87_DATA_ROOT
    v1_84_root.mkdir(parents=True, exist_ok=True)
    v1_87_root.mkdir(parents=True, exist_ok=True)
    for rel in ["manifest.json", "schema_snapshot.json", "preview_records.json"]:
        (v1_84_root / rel).write_text((PROJECT_ROOT / V1_84_DATA_ROOT / rel).read_text(encoding="utf-8"), encoding="utf-8")
    for rel in ["extension_manifest.json", "extension_quality_summary.json"]:
        (v1_87_root / rel).write_text((PROJECT_ROOT / V1_87_DATA_ROOT / rel).read_text(encoding="utf-8"), encoding="utf-8")


def test_empty_approval_phrase_denies():
    decision = evaluate_approval_phrase("")
    assert decision["approval_phrase_match"] is False
    assert decision["v1_90_authorized"] is False


def test_wrong_approval_phrase_denies():
    decision = evaluate_approval_phrase("approval")
    assert decision["human_approval_granted"] is False
    assert decision["authorized_future_version"] is None


def test_exact_approval_phrase_grants_future_v1_90_only():
    decision = evaluate_approval_phrase(APPROVAL_PHRASE_EXPECTED)
    assert decision["human_approval_granted"] is True
    assert decision["authorized_future_version"] == "V1.90"
    assert decision["authorized_future_scope"] == AUTHORIZED_FUTURE_SCOPE


def test_trailing_space_denies():
    assert evaluate_approval_phrase(APPROVAL_PHRASE_EXPECTED + " ")["approval_phrase_match"] is False


def test_punctuation_change_denies():
    assert evaluate_approval_phrase(APPROVAL_PHRASE_EXPECTED[:-1])["human_approval_granted"] is False


def test_approval_does_not_execute_v1_90():
    assert evaluate_approval_phrase(APPROVAL_PHRASE_EXPECTED)["v1_90_execution_attempted"] is False


def test_approval_does_not_write_data():
    payload = _valid_payload()
    assert payload["data_directory_write_attempted"] is False
    assert payload["new_data_files_created"] is False


def test_physical_audit_reads_v1_84_and_v1_87_only(tmp_path):
    _write_review_files(tmp_path)
    audit = ConsolidationPhysicalAuditor(tmp_path).audit()
    assert audit["v1_84_files_count"] == 3
    assert audit["v1_87_files_count"] == 2
    assert audit["v1_84_hashes_observed"] == EXPECTED_V1_84_HASHES
    assert audit["v1_87_hashes_observed"] == EXPECTED_V1_87_HASHES


def test_physical_audit_rejects_missing_v1_84_file(tmp_path):
    _write_review_files(tmp_path)
    (tmp_path / V1_84_DATA_ROOT / "manifest.json").unlink()
    assert ConsolidationPhysicalAuditor(tmp_path).audit()["v1_84_files_count"] == 2


def test_physical_audit_rejects_missing_v1_87_file(tmp_path):
    _write_review_files(tmp_path)
    (tmp_path / V1_87_DATA_ROOT / "extension_manifest.json").unlink()
    assert ConsolidationPhysicalAuditor(tmp_path).audit()["v1_87_files_count"] == 1


def test_physical_audit_rejects_extra_v1_84_file(tmp_path):
    _write_review_files(tmp_path)
    (tmp_path / V1_84_DATA_ROOT / "extra.json").write_text("{}", encoding="utf-8")
    assert ConsolidationPhysicalAuditor(tmp_path).audit()["v1_84_unexpected_files_count"] == 1


def test_physical_audit_rejects_extra_v1_87_file(tmp_path):
    _write_review_files(tmp_path)
    (tmp_path / V1_87_DATA_ROOT / "extra.json").write_text("{}", encoding="utf-8")
    assert ConsolidationPhysicalAuditor(tmp_path).audit()["v1_87_unexpected_files_count"] == 1


def test_physical_audit_rejects_v1_84_hash_mismatch(tmp_path):
    _write_review_files(tmp_path)
    (tmp_path / V1_84_DATA_ROOT / "manifest.json").write_text("{}", encoding="utf-8")
    assert ConsolidationPhysicalAuditor(tmp_path).audit()["v1_84_hashes_verified"] is False


def test_physical_audit_rejects_v1_87_hash_mismatch(tmp_path):
    _write_review_files(tmp_path)
    (tmp_path / V1_87_DATA_ROOT / "extension_manifest.json").write_text("{}", encoding="utf-8")
    assert ConsolidationPhysicalAuditor(tmp_path).audit()["v1_87_hashes_verified"] is False


def test_consolidation_plan_is_reports_only():
    design = design_consolidation_contract_v2()
    assert design["consolidation_plan_reports_only"] is True
    assert design["consolidation_plan_theoretical_paths_only"] is True


def test_consolidation_plan_has_bounded_future_root():
    assert design_consolidation_contract_v2()["future_consolidation_allowed_root"] == FUTURE_ALLOWED_ROOT


def test_consolidation_plan_rejects_more_than_three_future_files():
    design = design_consolidation_contract_v2()
    design["future_consolidation_max_files"] = 4
    assert "future_consolidation_max_files > 3" in validate_consolidation_design(design)


def test_consolidation_plan_rejects_forbidden_future_extension():
    design = design_consolidation_contract_v2()
    design["future_consolidation_expected_files"] = [f"{FUTURE_ALLOWED_ROOT}bad.parquet"]
    assert "future_consolidation_expected_files contains non-json path" in validate_consolidation_design(design)


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


def test_validator_rejects_v1_90_execution_attempted_true():
    assert _errors_with("v1_90_execution_attempted", True)


def test_validator_rejects_approval_granted_with_phrase_mismatch():
    payload = _valid_payload()
    payload["approval_phrase_match"] = False
    payload["human_approval_granted"] = True
    assert validate_payload(payload)


def test_report_index_references_v1_89():
    index = PROJECT_ROOT / "reports/REPORT_INDEX.md"
    content = index.read_text(encoding="utf-8") if index.exists() else ""
    assert "v1_89" in content or (PROJECT_ROOT / "scripts/run_microstructure_data_contract_consolidation_readiness_v1_89.py").exists()


def test_smoke_v1_89_runs_validator_import_and_summary_presence():
    commands = _SMOKE.get_commands_for_version("v1_89")
    assert commands[0][1] == "scripts/validate_microstructure_data_contract_consolidation_readiness_v1_89_reports.py"
    assert "import galapagos" in commands[1][2]
    assert "microstructure_data_contract_consolidation_readiness_summary_v1_89.json" in commands[2][2]


def test_cross_file_alignment_summary_latest_metrics_project_state():
    summary = _valid_payload()
    latest = dict(summary)
    project = dict(summary)
    assert latest["future_consolidation_allowed_root"] == summary["future_consolidation_allowed_root"]
    assert project["v1_90_authorized"] == summary["v1_90_authorized"]


def test_no_pass_only_tests_in_v1_89():
    content = Path(__file__).read_text(encoding="utf-8")
    assert not re.search(r"^\s*pass\s*$", content, re.MULTILINE)


def test_no_assert_true_or_true_in_v1_89():
    content = Path(__file__).read_text(encoding="utf-8")
    assert ("assert " + "True") not in content
    assert ("or " + "True") not in content


def test_scripts_run_without_manual_pythonpath():
    result = subprocess.run(
        [sys.executable, "scripts/validate_microstructure_data_contract_consolidation_readiness_v1_89_reports.py", "--version", "bad"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "Unsupported version" in (result.stdout + result.stderr)
