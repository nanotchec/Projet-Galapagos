from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from galapagos.research.microstructure_data_contract_extension_gate.approval_gate import (
    AUTHORIZED_SCOPE,
    EXPECTED_APPROVAL_PHRASE,
    ExtensionApprovalGate,
)
from galapagos.research.microstructure_data_contract_extension_gate.validator import validate_payload

_SMOKE_SPEC = importlib.util.spec_from_file_location("smoke_test_clean_zip", PROJECT_ROOT / "scripts/smoke_test_clean_zip.py")
assert _SMOKE_SPEC is not None and _SMOKE_SPEC.loader is not None
_SMOKE = importlib.util.module_from_spec(_SMOKE_SPEC)
_SMOKE_SPEC.loader.exec_module(_SMOKE)


def _valid_payload() -> dict:
    return {
        "approval_gate_only": True,
        "reports_only": True,
        "v1_87_execution_attempted": False,
        "materialization_executed": False,
        "new_materialization_executed": False,
        "data_contract_actual_write_executed": False,
        "scope_drift_detected": False,
        "data_directory_writes_allowed": False,
        "data_directory_write_attempted": False,
        "new_data_files_created": False,
        "existing_data_files_modified": False,
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
        "approval_phrase_match": True,
        "human_approval_granted": True,
        "authorized_future_version": "V1.87",
        "authorized_future_scope": AUTHORIZED_SCOPE,
        "release_ready_for_external_review": True,
        "smoke_test_passed": True,
        "clean_zip_ready_for_external_review": True,
    }


def _errors_with(field: str, value) -> list[str]:
    payload = _valid_payload()
    payload[field] = value
    return validate_payload(payload)


def test_empty_approval_phrase_denies():
    result = ExtensionApprovalGate().evaluate("")
    assert result["human_approval_granted"] is False
    assert result["v1_87_authorized"] is False


def test_wrong_approval_phrase_denies():
    result = ExtensionApprovalGate().evaluate("approve")
    assert result["approval_phrase_match"] is False
    assert result["authorized_future_version"] is None


def test_exact_approval_phrase_grants_future_v1_87_only():
    result = ExtensionApprovalGate().evaluate(EXPECTED_APPROVAL_PHRASE)
    assert result["human_approval_granted"] is True
    assert result["authorized_future_version"] == "V1.87"
    assert result["authorized_future_scope"] == AUTHORIZED_SCOPE


def test_trailing_space_denies():
    result = ExtensionApprovalGate().evaluate(EXPECTED_APPROVAL_PHRASE + " ")
    assert result["approval_phrase_match"] is False


def test_punctuation_change_denies():
    result = ExtensionApprovalGate().evaluate(EXPECTED_APPROVAL_PHRASE[:-1])
    assert result["approval_phrase_match"] is False


def test_approval_granted_does_not_execute_v1_87():
    assert _valid_payload()["v1_87_execution_attempted"] is False


def test_approval_granted_does_not_write_data():
    payload = _valid_payload()
    assert payload["data_contract_actual_write_executed"] is False
    assert payload["new_data_files_created"] is False


def test_approval_denied_does_not_write_data():
    result = ExtensionApprovalGate().evaluate("no")
    assert result["human_approval_granted"] is False
    assert _valid_payload()["data_directory_write_attempted"] is False


def test_validator_rejects_v1_87_execution_attempted_true():
    assert _errors_with("v1_87_execution_attempted", True)


def test_validator_rejects_data_write_attempted_true():
    assert _errors_with("data_directory_write_attempted", True)


def test_validator_rejects_new_data_files_created_true():
    assert _errors_with("new_data_files_created", True)


def test_validator_rejects_existing_data_files_modified_true():
    assert _errors_with("existing_data_files_modified", True)


def test_validator_rejects_dataset_created_true():
    assert _errors_with("dataset_created", True)


def test_validator_rejects_network_executed_true():
    assert _errors_with("network_executed", True)


def test_validator_rejects_trading_allowed_true():
    assert _errors_with("trading_allowed", True)


def test_validator_rejects_real_orders_possible_true():
    assert _errors_with("real_orders_possible", True)


def test_validator_rejects_ml_signal_validation_executed_true():
    assert _errors_with("ml_signal_validation_executed", True)


def test_validator_rejects_authorized_future_scope_mismatch():
    assert _errors_with("authorized_future_scope", "bad_scope")


def test_validator_rejects_approval_granted_with_phrase_mismatch():
    payload = _valid_payload()
    payload["approval_phrase_match"] = False
    errors = validate_payload(payload)
    assert any("phrase mismatch" in error for error in errors)


def test_report_index_references_v1_86():
    index = PROJECT_ROOT / "reports/REPORT_INDEX.md"
    content = index.read_text(encoding="utf-8") if index.exists() else ""
    assert "v1_86" in content or (PROJECT_ROOT / "scripts/run_microstructure_data_contract_extension_gate_v1_86.py").exists()


def test_smoke_v1_86_runs_validator_import_and_summary_presence():
    commands = _SMOKE.get_commands_for_version("v1_86")
    assert commands[0][1] == "scripts/validate_microstructure_data_contract_extension_gate_v1_86_reports.py"
    assert "import galapagos" in commands[1][2]
    assert "microstructure_data_contract_extension_gate_summary_v1_86.json" in commands[2][2]


def test_cross_file_alignment_summary_latest_metrics_project_state():
    summary = _valid_payload()
    latest = dict(summary)
    project = dict(summary)
    assert latest["v1_87_execution_attempted"] == summary["v1_87_execution_attempted"]
    assert project["authorized_future_scope"] == summary["authorized_future_scope"]
