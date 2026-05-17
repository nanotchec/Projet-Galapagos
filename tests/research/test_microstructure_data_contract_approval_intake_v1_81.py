import pytest
from galapagos.research.microstructure_data_contract_approval_intake.approval_intake import ApprovalIntake
from galapagos.research.microstructure_data_contract_approval_intake.safety_guard import SafetyGuard

def test_approval_intake_success():
    intake = ApprovalIntake()
    phrase = "J'approuve V1.82 dry-run data contract reports-only, sans écriture data, sans dataset, sans trading."
    res = intake.validate_approval(phrase)
    assert res["approval_phrase_match"] is True
    assert res["human_approval_granted"] is True
    assert res["v1_82_authorized"] is True

def test_approval_intake_empty():
    intake = ApprovalIntake()
    res = intake.validate_approval("")
    assert res["approval_phrase_match"] is False
    assert res["human_approval_granted"] is False

def test_approval_intake_mismatch():
    intake = ApprovalIntake()
    res = intake.validate_approval("Incorrect phrase")
    assert res["approval_phrase_match"] is False
    assert res["human_approval_granted"] is False

def test_safety_guard_passed():
    guard = SafetyGuard()
    state = {
        "network_executed": False,
        "new_network_requests_executed": False,
        "data_directory_writes_allowed": False,
        "new_data_files_created": False,
        "no_data_directory_writes": True,
        "dataset_created": False,
        "parquet_created": False,
        "csv_created": False,
        "sqlite_created": False,
        "jsonl_created": False,
        "db_created": False,
        "trading_allowed": False,
        "real_orders_possible": False,
        "no_real_trading": True,
        "no_paper_live": True,
        "data_write_approved": False,
        "dataset_materialization_approved": False
    }
    res = guard.check_safety(state)
    assert res["safety_check_passed"] is True

def test_safety_guard_network_fail():
    guard = SafetyGuard()
    state = {"network_executed": True}
    res = guard.check_safety(state)
    assert res["safety_check_passed"] is False

def test_safety_guard_data_write_fail():
    guard = SafetyGuard()
    state = {"new_data_files_created": True, "no_data_directory_writes": False}
    res = guard.check_safety(state)
    assert res["safety_check_passed"] is False

def test_safety_guard_dataset_fail():
    guard = SafetyGuard()
    state = {"dataset_created": True}
    res = guard.check_safety(state)
    assert res["safety_check_passed"] is False

def test_safety_guard_trading_fail():
    guard = SafetyGuard()
    state = {"trading_allowed": True, "real_orders_possible": True}
    res = guard.check_safety(state)
    assert res["safety_check_passed"] is False

def test_safety_guard_approval_leak_fail():
    guard = SafetyGuard()
    state = {"data_write_approved": True}
    res = guard.check_safety(state)
    assert res["safety_check_passed"] is False
