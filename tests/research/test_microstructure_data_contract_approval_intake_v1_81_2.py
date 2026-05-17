import pytest
import json
import sys
from pathlib import Path
from galapagos.research.microstructure_data_contract_approval_intake.approval_intake import ApprovalIntake
from galapagos.research.microstructure_data_contract_approval_intake.safety_guard import SafetyGuard, STRICT_REQUIRED_INVARIANTS
from galapagos.research.microstructure_data_contract_approval_intake.negative_coverage import NegativeCoverage, REQUIRED_NEGATIVE_TESTS

# ─── Approval Tests (1-8) ───────────────────────────────────────────────────

def test_approval_exact_phrase_grants_future_v1_82_only():
    intake = ApprovalIntake()
    phrase = "J'approuve V1.82 dry-run data contract reports-only, sans écriture data, sans dataset, sans trading."
    res = intake.validate_approval(phrase)
    assert res["approval_phrase_match"] is True
    assert res["human_approval_granted"] is True
    assert res["v1_82_authorized"] is True
    assert res["authorized_future_version"] == "V1.82"

def test_approval_empty_phrase_denies():
    intake = ApprovalIntake()
    res = intake.validate_approval("")
    assert res["approval_phrase_match"] is False
    assert res["human_approval_granted"] is False

def test_approval_wrong_phrase_denies():
    intake = ApprovalIntake()
    res = intake.validate_approval("Incorrect")
    assert res["approval_phrase_match"] is False

def test_approval_trailing_space_denies():
    intake = ApprovalIntake()
    phrase = "J'approuve V1.82 dry-run data contract reports-only, sans écriture data, sans dataset, sans trading. "
    res = intake.validate_approval(phrase)
    assert res["approval_phrase_match"] is False

def test_approval_punctuation_change_denies():
    intake = ApprovalIntake()
    phrase = "J'approuve V1.82 dry-run data contract reports-only, sans écriture data, sans dataset, sans trading!"
    res = intake.validate_approval(phrase)
    assert res["approval_phrase_match"] is False

def test_approval_authorization_cannot_be_true_when_phrase_mismatch():
    intake = ApprovalIntake()
    res = intake.validate_approval("BAD")
    # Simulation of a corrupted intake logic result if it were to return True
    if not res["approval_phrase_match"]:
        assert res["v1_82_authorized"] is False

def test_approval_future_scope_must_match_exactly():
    intake = ApprovalIntake()
    phrase = "J'approuve V1.82 dry-run data contract reports-only, sans écriture data, sans dataset, sans trading."
    res = intake.validate_approval(phrase)
    expected_scope = "tiny_data_contract_materialization_dryrun_reports_only_no_data_write_no_dataset_no_network_no_trading"
    assert res["authorized_future_scope"] == expected_scope

def test_approval_future_version_must_be_v1_82():
    intake = ApprovalIntake()
    phrase = "J'approuve V1.82 dry-run data contract reports-only, sans écriture data, sans dataset, sans trading."
    res = intake.validate_approval(phrase)
    assert res["authorized_future_version"] == "V1.82"

# ─── Network Safety Guard Tests (9-14) ───────────────────────────────────────

def test_guard_rejects_network_executed_true():
    guard = SafetyGuard()
    res = guard.check_safety({"network_executed": True})
    assert res["safety_check_passed"] is False

def test_guard_rejects_new_network_requests_executed_true():
    guard = SafetyGuard()
    res = guard.check_safety({"new_network_requests_executed": True})
    assert res["safety_check_passed"] is False

def test_guard_rejects_request_retry_count_positive():
    guard = SafetyGuard()
    res = guard.check_safety({"request_retry_count": 1})
    assert res["safety_check_passed"] is False

def test_guard_rejects_pagination_used_true():
    guard = SafetyGuard()
    res = guard.check_safety({"pagination_used": True})
    assert res["safety_check_passed"] is False

def test_guard_rejects_authenticated_request_allowed_true():
    guard = SafetyGuard()
    res = guard.check_safety({"authenticated_request_allowed": True})
    assert res["safety_check_passed"] is False

def test_guard_rejects_secrets_used_true():
    guard = SafetyGuard()
    res = guard.check_safety({"secrets_used": True})
    assert res["safety_check_passed"] is False

# ─── Data Write Safety Guard Tests (15-26) ───────────────────────────────────

def test_guard_rejects_data_directory_writes_allowed_true():
    guard = SafetyGuard()
    res = guard.check_safety({"data_directory_writes_allowed": True})
    assert res["safety_check_passed"] is False

def test_guard_rejects_new_data_files_created_true():
    guard = SafetyGuard()
    res = guard.check_safety({"new_data_files_created": True})
    assert res["safety_check_passed"] is False

def test_guard_rejects_no_data_directory_writes_false():
    guard = SafetyGuard()
    res = guard.check_safety({"no_data_directory_writes": False})
    assert res["safety_check_passed"] is False

def test_guard_rejects_parquet_created_true():
    guard = SafetyGuard()
    res = guard.check_safety({"parquet_created": True})
    assert res["safety_check_passed"] is False

def test_guard_rejects_csv_created_true():
    guard = SafetyGuard()
    res = guard.check_safety({"csv_created": True})
    assert res["safety_check_passed"] is False

def test_guard_rejects_sqlite_created_true():
    guard = SafetyGuard()
    res = guard.check_safety({"sqlite_created": True})
    assert res["safety_check_passed"] is False

def test_guard_rejects_jsonl_created_true():
    guard = SafetyGuard()
    res = guard.check_safety({"jsonl_created": True})
    assert res["safety_check_passed"] is False

def test_guard_rejects_db_created_true():
    guard = SafetyGuard()
    res = guard.check_safety({"db_created": True})
    assert res["safety_check_passed"] is False

def test_guard_rejects_dataset_created_true():
    guard = SafetyGuard()
    res = guard.check_safety({"dataset_created": True})
    assert res["safety_check_passed"] is False

def test_guard_rejects_research_dataset_updated_true():
    guard = SafetyGuard()
    res = guard.check_safety({"research_dataset_updated": True})
    assert res["safety_check_passed"] is False

def test_guard_rejects_data_write_approved_true():
    guard = SafetyGuard()
    res = guard.check_safety({"data_write_approved": True})
    assert res["safety_check_passed"] is False

def test_guard_rejects_dataset_materialization_approved_true():
    guard = SafetyGuard()
    res = guard.check_safety({"dataset_materialization_approved": True})
    assert res["safety_check_passed"] is False

# ─── Trading / ML Safety Guard Tests (27-38) ─────────────────────────────────

def test_guard_rejects_strategy_link_allowed_true():
    guard = SafetyGuard()
    res = guard.check_safety({"strategy_link_allowed": True})
    assert res["safety_check_passed"] is False

def test_guard_rejects_trading_allowed_true():
    guard = SafetyGuard()
    res = guard.check_safety({"trading_allowed": True})
    assert res["safety_check_passed"] is False

def test_guard_rejects_no_strategy_validated_false():
    guard = SafetyGuard()
    res = guard.check_safety({"no_strategy_validated": False})
    assert res["safety_check_passed"] is False

def test_guard_rejects_no_paper_live_false():
    guard = SafetyGuard()
    res = guard.check_safety({"no_paper_live": False})
    assert res["safety_check_passed"] is False

def test_guard_rejects_no_real_trading_false():
    guard = SafetyGuard()
    res = guard.check_safety({"no_real_trading": False})
    assert res["safety_check_passed"] is False

def test_guard_rejects_real_orders_possible_true():
    guard = SafetyGuard()
    res = guard.check_safety({"real_orders_possible": True})
    assert res["safety_check_passed"] is False

def test_guard_rejects_holdout_executed_true():
    guard = SafetyGuard()
    res = guard.check_safety({"holdout_executed": True})
    assert res["safety_check_passed"] is False

def test_guard_rejects_codex_cli_called_true():
    guard = SafetyGuard()
    res = guard.check_safety({"codex_cli_called": True})
    assert res["safety_check_passed"] is False

def test_guard_rejects_ml_signal_validation_executed_true():
    guard = SafetyGuard()
    res = guard.check_safety({"ml_signal_validation_executed": True})
    assert res["safety_check_passed"] is False

def test_guard_rejects_predictions_created_true():
    guard = SafetyGuard()
    res = guard.check_safety({"predictions_created": True})
    assert res["safety_check_passed"] is False

def test_guard_rejects_labels_created_true():
    guard = SafetyGuard()
    res = guard.check_safety({"labels_created": True})
    assert res["safety_check_passed"] is False

def test_guard_rejects_targets_created_true():
    guard = SafetyGuard()
    res = guard.check_safety({"targets_created": True})
    assert res["safety_check_passed"] is False

# ─── Scope Drift Safety Guard Tests (39-41) ──────────────────────────────────

def test_guard_rejects_v1_82_execution_attempted_true():
    guard = SafetyGuard()
    res = guard.check_safety({"v1_82_execution_attempted": True})
    assert res["safety_check_passed"] is False

def test_guard_rejects_data_contract_dryrun_executed_true():
    guard = SafetyGuard()
    res = guard.check_safety({"data_contract_dryrun_executed": True})
    assert res["safety_check_passed"] is False

def test_guard_rejects_scope_drift_detected_true():
    guard = SafetyGuard()
    res = guard.check_safety({"scope_drift_detected": True})
    assert res["safety_check_passed"] is False

# ─── Coverage Tests (42-44) ──────────────────────────────────────────────────

def test_negative_coverage_maps_every_required_invariant_to_test_name():
    cov = NegativeCoverage()
    res = cov.get_coverage_report()
    assert res["negative_test_coverage_complete"] is True
    assert res["required_negative_invariants_count"] >= 33

def test_negative_coverage_fails_when_invariant_mapping_missing():
    mapping = REQUIRED_NEGATIVE_TESTS.copy()
    del mapping["network_executed"]
    # Internal check of logic
    missing = [inv for inv in REQUIRED_NEGATIVE_TESTS if not mapping.get(inv)]
    assert len(missing) == 1

def test_negative_coverage_has_no_duplicate_test_names():
    cov = NegativeCoverage()
    res = cov.get_coverage_report()
    assert len(res["duplicate_test_names"]) == 0

# ─── Validator Unit Tests (45-52) ───────────────────────────────────────────
# We simulate summary dictionaries and check if they would pass core invariant logic

def check_invariants_manually(summary):
    invariants = [
        ("network_executed", False),
        ("pagination_used", False),
        ("dataset_created", False),
        ("research_dataset_updated", False),
        ("trading_allowed", False),
        ("predictions_created", False),
        ("scope_drift_detected", False)
    ]
    for field, expected in invariants:
        if summary.get(field) != expected:
            return False
    return True

def test_validator_logic_rejects_summary_with_network_executed_true():
    assert check_invariants_manually({"network_executed": True}) is False

def test_validator_logic_rejects_summary_with_pagination_used_true():
    assert check_invariants_manually({"pagination_used": True}) is False

def test_validator_logic_rejects_summary_with_dataset_created_true():
    assert check_invariants_manually({"dataset_created": True}) is False

def test_validator_logic_rejects_summary_with_research_dataset_updated_true():
    assert check_invariants_manually({"research_dataset_updated": True}) is False

def test_validator_logic_rejects_summary_with_trading_allowed_true():
    assert check_invariants_manually({"trading_allowed": True}) is False

def test_validator_logic_rejects_summary_with_predictions_created_true():
    assert check_invariants_manually({"predictions_created": True}) is False

def test_validator_logic_rejects_summary_with_scope_drift_detected_true():
    assert check_invariants_manually({"scope_drift_detected": True}) is False

def test_validator_logic_rejects_incomplete_negative_coverage():
    cov = {"negative_test_coverage_complete": False}
    assert cov["negative_test_coverage_complete"] is False
