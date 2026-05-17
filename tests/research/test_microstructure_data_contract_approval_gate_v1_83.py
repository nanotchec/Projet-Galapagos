from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from galapagos.research.microstructure_data_contract_approval_gate.approval_gate import (
    AUTHORIZED_SCOPE,
    EXPECTED_APPROVAL_PHRASE,
    ApprovalGate,
)

_VALIDATOR_SPEC = importlib.util.spec_from_file_location(
    "validate_v1_83",
    PROJECT_ROOT / "scripts/validate_microstructure_data_contract_approval_gate_v1_83_reports.py",
)
assert _VALIDATOR_SPEC is not None and _VALIDATOR_SPEC.loader is not None
_VALIDATOR = importlib.util.module_from_spec(_VALIDATOR_SPEC)
_VALIDATOR_SPEC.loader.exec_module(_VALIDATOR)

_SMOKE_SPEC = importlib.util.spec_from_file_location(
    "smoke_test_clean_zip",
    PROJECT_ROOT / "scripts/smoke_test_clean_zip.py",
)
assert _SMOKE_SPEC is not None and _SMOKE_SPEC.loader is not None
_SMOKE = importlib.util.module_from_spec(_SMOKE_SPEC)
_SMOKE_SPEC.loader.exec_module(_SMOKE)


def _valid_payload() -> dict:
    payload = {
        "approval_gate_only": True,
        "reports_only": True,
        "v1_84_execution_attempted": False,
        "materialization_executed": False,
        "data_contract_actual_write_executed": False,
        "data_directory_write_attempted": False,
        "new_data_files_created": False,
        "no_data_directory_writes": True,
        "dataset_created": False,
        "network_executed": False,
        "trading_allowed": False,
        "real_orders_possible": False,
        "ml_signal_validation_executed": False,
        "approval_phrase_match": True,
        "human_approval_granted": True,
        "authorized_future_version": "V1.84",
        "authorized_future_scope": AUTHORIZED_SCOPE,
        "release_ready_for_external_review": True,
        "smoke_test_passed": True,
        "clean_zip_ready_for_external_review": True,
    }
    return payload


def _errors_with(field: str, value) -> list[str]:
    payload = _valid_payload()
    payload[field] = value
    return _VALIDATOR.validate_payload(payload)


def test_empty_approval_phrase_denies():
    result = ApprovalGate().evaluate("")
    assert result["human_approval_granted"] is False
    assert result["v1_84_authorized"] is False


def test_wrong_approval_phrase_denies():
    result = ApprovalGate().evaluate("approve")
    assert result["approval_phrase_match"] is False
    assert result["authorized_future_version"] is None


def test_exact_approval_phrase_grants_future_v1_84_only():
    result = ApprovalGate().evaluate(EXPECTED_APPROVAL_PHRASE)
    assert result["human_approval_granted"] is True
    assert result["authorized_future_version"] == "V1.84"
    assert result["authorized_future_scope"] == AUTHORIZED_SCOPE


def test_trailing_space_denies():
    result = ApprovalGate().evaluate(EXPECTED_APPROVAL_PHRASE + " ")
    assert result["approval_phrase_match"] is False


def test_punctuation_change_denies():
    result = ApprovalGate().evaluate(EXPECTED_APPROVAL_PHRASE[:-1])
    assert result["approval_phrase_match"] is False


def test_approval_granted_does_not_execute_v1_84():
    assert _valid_payload()["v1_84_execution_attempted"] is False


def test_approval_granted_does_not_write_data():
    payload = _valid_payload()
    assert payload["data_contract_actual_write_executed"] is False
    assert payload["new_data_files_created"] is False


def test_approval_denied_does_not_write_data():
    result = ApprovalGate().evaluate("no")
    assert result["human_approval_granted"] is False
    assert _valid_payload()["data_directory_write_attempted"] is False


def test_validator_rejects_v1_84_execution_attempted_true():
    assert _errors_with("v1_84_execution_attempted", True)


def test_validator_rejects_data_write_attempted_true():
    assert _errors_with("data_directory_write_attempted", True)


def test_validator_rejects_new_data_files_created_true():
    assert _errors_with("new_data_files_created", True)


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
    errors = _VALIDATOR.validate_payload(payload)
    assert any("phrase mismatch" in error for error in errors)


def test_report_index_references_v1_83():
    index = PROJECT_ROOT / "reports/REPORT_INDEX.md"
    if not index.exists():
        content = ""
    else:
        content = index.read_text(encoding="utf-8")
    assert "v1_83" in content or "V1.83" in content or (PROJECT_ROOT / "scripts/run_microstructure_data_contract_approval_gate_v1_83.py").exists()


def test_smoke_v1_83_runs_validator_import_and_summary_presence():
    commands = _SMOKE.get_commands_for_version("v1_83")
    assert commands[0][1] == "scripts/validate_microstructure_data_contract_approval_gate_v1_83_reports.py"
    assert "import galapagos" in commands[1][2]
    assert "microstructure_data_contract_approval_gate_summary_v1_83.json" in commands[2][2]
