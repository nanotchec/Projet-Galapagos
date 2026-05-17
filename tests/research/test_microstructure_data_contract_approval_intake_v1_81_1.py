import pytest
from galapagos.research.microstructure_data_contract_approval_intake.approval_intake import ApprovalIntake
from galapagos.research.microstructure_data_contract_approval_intake.safety_guard import SafetyGuard
from galapagos.research.microstructure_data_contract_approval_intake.corrective_audit import CorrectiveAudit
from galapagos.research.microstructure_data_contract_approval_intake.negative_coverage import NegativeCoverage

def test_approval_exact_success():
    intake = ApprovalIntake()
    phrase = "J'approuve V1.82 dry-run data contract reports-only, sans écriture data, sans dataset, sans trading."
    res = intake.validate_approval(phrase)
    assert res["approval_phrase_match"] is True

def test_approval_trailing_space_fail():
    intake = ApprovalIntake()
    phrase = "J'approuve V1.82 dry-run data contract reports-only, sans écriture data, sans dataset, sans trading. "
    res = intake.validate_approval(phrase)
    assert res["approval_phrase_match"] is False

def test_approval_punctuation_fail():
    intake = ApprovalIntake()
    phrase = "J'approuve V1.82 dry-run data contract reports-only, sans écriture data, sans dataset, sans trading!"
    res = intake.validate_approval(phrase)
    assert res["approval_phrase_match"] is False

def test_safety_guard_network_neg():
    guard = SafetyGuard()
    assert guard.check_safety({"network_executed": True})["safety_check_passed"] is False
    assert guard.check_safety({"new_network_requests_executed": True})["safety_check_passed"] is False
    assert guard.check_safety({"request_retry_count": 1})["safety_check_passed"] is False

def test_safety_guard_data_neg():
    guard = SafetyGuard()
    assert guard.check_safety({"data_directory_writes_allowed": True})["safety_check_passed"] is False
    assert guard.check_safety({"new_data_files_created": True})["safety_check_passed"] is False
    assert guard.check_safety({"parquet_created": True})["safety_check_passed"] is False
    assert guard.check_safety({"csv_created": True})["safety_check_passed"] is False
    assert guard.check_safety({"dataset_created": True})["safety_check_passed"] is False

def test_safety_guard_trading_neg():
    guard = SafetyGuard()
    assert guard.check_safety({"trading_allowed": True})["safety_check_passed"] is False
    assert guard.check_safety({"real_orders_possible": True})["safety_check_passed"] is False
    assert guard.check_safety({"no_real_trading": False})["safety_check_passed"] is False

def test_corrective_audit_scope_drift_neg():
    audit = CorrectiveAudit()
    assert audit.audit_v1_81_1_state({"v1_82_execution_attempted": True})["corrective_audit_passed"] is False
    assert audit.audit_v1_81_1_state({"data_contract_dryrun_executed": True})["corrective_audit_passed"] is False

def test_negative_coverage_completeness():
    coverage = NegativeCoverage()
    res = coverage.get_coverage_report()
    assert res["negative_test_coverage_complete"] is True
    assert res["required_negative_invariants_count"] >= 33
    assert len(res["missing_negative_invariants"]) == 0
