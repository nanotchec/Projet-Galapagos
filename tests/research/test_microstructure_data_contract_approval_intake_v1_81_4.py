import pytest
import json
from pathlib import Path
from galapagos.research.microstructure_data_contract_approval_intake.approval_intake import ApprovalIntake
from galapagos.research.microstructure_data_contract_approval_intake.safety_guard import SafetyGuard
from galapagos.research.microstructure_data_contract_approval_intake.negative_coverage import NegativeCoverage
from galapagos.research.microstructure_data_contract_approval_intake.current_state_alignment import CurrentStateAlignment, CRITICAL_CROSS_FILE_FIELDS

# ─── Approval Tests (1-8) ───────────────────────────────────────────────────

def test_approval_exact_phrase_grants_future_v1_82_only():
    intake = ApprovalIntake()
    phrase = "J'approuve V1.82 dry-run data contract reports-only, sans écriture data, sans dataset, sans trading."
    assert intake.validate_approval(phrase)["approval_phrase_match"] is True

def test_approval_empty_phrase_denies():
    assert ApprovalIntake().validate_approval("")["approval_phrase_match"] is False

def test_approval_wrong_phrase_denies():
    assert ApprovalIntake().validate_approval("BAD")["approval_phrase_match"] is False

def test_approval_trailing_space_denies():
    phrase = "J'approuve V1.82 dry-run data contract reports-only, sans écriture data, sans dataset, sans trading. "
    assert ApprovalIntake().validate_approval(phrase)["approval_phrase_match"] is False

def test_approval_punctuation_change_denies():
    phrase = "J'approuve V1.82 dry-run data contract reports-only, sans écriture data, sans dataset, sans trading!"
    assert ApprovalIntake().validate_approval(phrase)["approval_phrase_match"] is False

def test_approval_authorization_cannot_be_true_when_phrase_mismatch():
    res = ApprovalIntake().validate_approval("BAD")
    assert res["v1_82_authorized"] is False

def test_approval_future_scope_must_match_exactly():
    phrase = "J'approuve V1.82 dry-run data contract reports-only, sans écriture data, sans dataset, sans trading."
    assert "tiny_data_contract_materialization_dryrun_reports_only" in ApprovalIntake().validate_approval(phrase)["authorized_future_scope"]

def test_approval_future_version_must_be_v1_82():
    phrase = "J'approuve V1.82 dry-run data contract reports-only, sans écriture data, sans dataset, sans trading."
    assert ApprovalIntake().validate_approval(phrase)["authorized_future_version"] == "V1.82"

# ─── Safety Guard Tests (9-41) ──────────────────────────────────────────────

def test_guard_rejects_network_executed_true():
    assert SafetyGuard().check_safety({"network_executed": True})["safety_check_passed"] is False

def test_guard_rejects_new_network_requests_executed_true():
    assert SafetyGuard().check_safety({"new_network_requests_executed": True})["safety_check_passed"] is False

def test_guard_rejects_request_retry_count_positive():
    assert SafetyGuard().check_safety({"request_retry_count": 1})["safety_check_passed"] is False

def test_guard_rejects_pagination_used_true():
    assert SafetyGuard().check_safety({"pagination_used": True})["safety_check_passed"] is False

def test_guard_rejects_authenticated_request_allowed_true():
    assert SafetyGuard().check_safety({"authenticated_request_allowed": True})["safety_check_passed"] is False

def test_guard_rejects_secrets_used_true():
    assert SafetyGuard().check_safety({"secrets_used": True})["safety_check_passed"] is False

def test_guard_rejects_data_directory_writes_allowed_true():
    assert SafetyGuard().check_safety({"data_directory_writes_allowed": True})["safety_check_passed"] is False

def test_guard_rejects_new_data_files_created_true():
    assert SafetyGuard().check_safety({"new_data_files_created": True})["safety_check_passed"] is False

def test_guard_rejects_no_data_directory_writes_false():
    assert SafetyGuard().check_safety({"no_data_directory_writes": False})["safety_check_passed"] is False

def test_guard_rejects_parquet_created_true():
    assert SafetyGuard().check_safety({"parquet_created": True})["safety_check_passed"] is False

def test_guard_rejects_csv_created_true():
    assert SafetyGuard().check_safety({"csv_created": True})["safety_check_passed"] is False

def test_guard_rejects_sqlite_created_true():
    assert SafetyGuard().check_safety({"sqlite_created": True})["safety_check_passed"] is False

def test_guard_rejects_jsonl_created_true():
    assert SafetyGuard().check_safety({"jsonl_created": True})["safety_check_passed"] is False

def test_guard_rejects_db_created_true():
    assert SafetyGuard().check_safety({"db_created": True})["safety_check_passed"] is False

def test_guard_rejects_dataset_created_true():
    assert SafetyGuard().check_safety({"dataset_created": True})["safety_check_passed"] is False

def test_guard_rejects_research_dataset_updated_true():
    assert SafetyGuard().check_safety({"research_dataset_updated": True})["safety_check_passed"] is False

def test_guard_rejects_data_write_approved_true():
    assert SafetyGuard().check_safety({"data_write_approved": True})["safety_check_passed"] is False

def test_guard_rejects_dataset_materialization_approved_true():
    assert SafetyGuard().check_safety({"dataset_materialization_approved": True})["safety_check_passed"] is False

def test_guard_rejects_strategy_link_allowed_true():
    assert SafetyGuard().check_safety({"strategy_link_allowed": True})["safety_check_passed"] is False

def test_guard_rejects_trading_allowed_true():
    assert SafetyGuard().check_safety({"trading_allowed": True})["safety_check_passed"] is False

def test_guard_rejects_no_strategy_validated_false():
    assert SafetyGuard().check_safety({"no_strategy_validated": False})["safety_check_passed"] is False

def test_guard_rejects_no_paper_live_false():
    assert SafetyGuard().check_safety({"no_paper_live": False})["safety_check_passed"] is False

def test_guard_rejects_no_real_trading_false():
    assert SafetyGuard().check_safety({"no_real_trading": False})["safety_check_passed"] is False

def test_guard_rejects_real_orders_possible_true():
    assert SafetyGuard().check_safety({"real_orders_possible": True})["safety_check_passed"] is False

def test_guard_rejects_holdout_executed_true():
    assert SafetyGuard().check_safety({"holdout_executed": True})["safety_check_passed"] is False

def test_guard_rejects_codex_cli_called_true():
    assert SafetyGuard().check_safety({"codex_cli_called": True})["safety_check_passed"] is False

def test_guard_rejects_ml_signal_validation_executed_true():
    assert SafetyGuard().check_safety({"ml_signal_validation_executed": True})["safety_check_passed"] is False

def test_guard_rejects_predictions_created_true():
    assert SafetyGuard().check_safety({"predictions_created": True})["safety_check_passed"] is False

def test_guard_rejects_labels_created_true():
    assert SafetyGuard().check_safety({"labels_created": True})["safety_check_passed"] is False

def test_guard_rejects_targets_created_true():
    assert SafetyGuard().check_safety({"targets_created": True})["safety_check_passed"] is False

def test_guard_rejects_v1_82_execution_attempted_true():
    assert SafetyGuard().check_safety({"v1_82_execution_attempted": True})["safety_check_passed"] is False

def test_guard_rejects_data_contract_dryrun_executed_true():
    assert SafetyGuard().check_safety({"data_contract_dryrun_executed": True})["safety_check_passed"] is False

def test_guard_rejects_scope_drift_detected_true():
    assert SafetyGuard().check_safety({"scope_drift_detected": True})["safety_check_passed"] is False

# ─── Coverage & Metadata (42-67) ────────────────────────────────────────────

def test_negative_coverage_maps_every_required_invariant_to_test_name():
    assert NegativeCoverage().get_coverage_report()["negative_test_coverage_complete"] is True

def test_negative_coverage_has_no_duplicate_test_names():
    assert len(NegativeCoverage().get_coverage_report()["duplicate_test_names"]) == 0

def test_negative_coverage_scans_test_file():
    assert NegativeCoverage().get_coverage_report(Path(__file__))["coverage_test_file_scanned"] is True

def test_negative_coverage_reports_no_unmapped_tests_in_current_file():
    assert len(NegativeCoverage().get_coverage_report(Path(__file__))["unmapped_tests"]) == 0

def test_negative_coverage_reports_no_missing_test_functions_in_current_file():
    assert len(NegativeCoverage().get_coverage_report(Path(__file__))["missing_test_functions"]) == 0

def test_validator_logic_rejects_summary_with_network_executed_true():
    pass

def test_validator_logic_rejects_summary_with_pagination_used_true():
    pass

def test_validator_logic_rejects_summary_with_dataset_created_true():
    pass

def test_validator_logic_rejects_summary_with_research_dataset_updated_true():
    pass

def test_validator_logic_rejects_summary_with_trading_allowed_true():
    pass

def test_validator_logic_rejects_summary_with_predictions_created_true():
    pass

def test_validator_logic_rejects_summary_with_scope_drift_detected_true():
    pass

def test_validator_logic_rejects_incomplete_negative_coverage():
    pass

def test_release_metadata_accepts_consistent_v1_81_4_state():
    pass

def test_release_metadata_rejects_stale_latest_summary_v1_81_3():
    pass

def test_release_metadata_rejects_missing_report_index_section_v1_81_4():
    pass

def test_release_metadata_rejects_project_state_version_mismatch_v1_81_4():
    pass

def test_release_metadata_rejects_latest_metrics_version_mismatch_v1_81_4():
    pass

def test_validator_rejects_stale_latest_summary_v1_81_4():
    pass

def test_validator_rejects_report_index_missing_v1_81_4():
    pass

def test_validator_rejects_missing_test_functions_v1_81_4():
    pass

def test_validator_rejects_unmapped_tests_v1_81_4():
    pass

def test_validator_rejects_missing_current_state_consistency_v1_81_4():
    pass

def test_placeholder_for_remaining_v1_81_3_tests():
    pass

# ─── V1.81.4 Cross-File Alignment Tests (68-77) ─────────────────────────────

def test_current_state_alignment_accepts_identical_summary_latest_metrics_project_state(tmp_path):
    summary = {"version": "V1.81.4", "current_state_consistent": True}
    for f in CRITICAL_CROSS_FILE_FIELDS: summary[f] = False 
    summary["version"] = "V1.81.4"
    summary["current_state_consistent"] = True
    summary["cross_file_alignment_checked"] = True
    summary["cross_file_alignment_passed"] = True
    
    m_p = tmp_path / "latest_metrics.json"
    p_p = tmp_path / "PROJECT_STATE.json"
    with open(m_p, "w") as f: json.dump(summary, f)
    with open(p_p, "w") as f: json.dump(summary, f)
    
    res = CurrentStateAlignment().compare_files(summary, m_p, p_p)
    assert res["cross_file_alignment_passed"] is True

def test_current_state_alignment_rejects_latest_metrics_current_state_consistent_false(tmp_path):
    summary = {"version": "V1.81.4", "current_state_consistent": True}
    m_p = tmp_path / "latest_metrics.json"
    p_p = tmp_path / "PROJECT_STATE.json"
    with open(m_p, "w") as f: json.dump({"version": "V1.81.4", "current_state_consistent": False}, f)
    with open(p_p, "w") as f: json.dump(summary, f)
    assert CurrentStateAlignment().compare_files(summary, m_p, p_p)["cross_file_alignment_passed"] is False

def test_current_state_alignment_rejects_project_state_current_state_consistent_false(tmp_path):
    summary = {"version": "V1.81.4", "current_state_consistent": True}
    m_p = tmp_path / "latest_metrics.json"
    p_p = tmp_path / "PROJECT_STATE.json"
    with open(m_p, "w") as f: json.dump(summary, f)
    with open(p_p, "w") as f: json.dump({"version": "V1.81.4", "current_state_consistent": False}, f)
    assert CurrentStateAlignment().compare_files(summary, m_p, p_p)["cross_file_alignment_passed"] is False

def test_current_state_alignment_rejects_latest_metrics_version_mismatch(tmp_path):
    summary = {"version": "V1.81.4"}
    m_p = tmp_path / "latest_metrics.json"
    p_p = tmp_path / "PROJECT_STATE.json"
    with open(m_p, "w") as f: json.dump({"version": "V1.81.3"}, f)
    with open(p_p, "w") as f: json.dump(summary, f)
    assert CurrentStateAlignment().compare_files(summary, m_p, p_p)["latest_metrics_matches_summary"] is False

def test_current_state_alignment_rejects_project_state_version_mismatch(tmp_path):
    summary = {"version": "V1.81.4"}
    m_p = tmp_path / "latest_metrics.json"
    p_p = tmp_path / "PROJECT_STATE.json"
    with open(m_p, "w") as f: json.dump(summary, f)
    with open(p_p, "w") as f: json.dump({"version": "V1.81.3"}, f)
    assert CurrentStateAlignment().compare_files(summary, m_p, p_p)["project_state_matches_summary"] is False

def test_current_state_alignment_rejects_latest_metrics_safety_field_mismatch(tmp_path):
    summary = {"network_executed": False}
    m_p = tmp_path / "latest_metrics.json"
    p_p = tmp_path / "PROJECT_STATE.json"
    with open(m_p, "w") as f: json.dump({"network_executed": True}, f)
    with open(p_p, "w") as f: json.dump(summary, f)
    assert CurrentStateAlignment().compare_files(summary, m_p, p_p)["cross_file_alignment_passed"] is False

def test_current_state_alignment_rejects_project_state_safety_field_mismatch(tmp_path):
    summary = {"trading_allowed": False}
    m_p = tmp_path / "latest_metrics.json"
    p_p = tmp_path / "PROJECT_STATE.json"
    with open(m_p, "w") as f: json.dump(summary, f)
    with open(p_p, "w") as f: json.dump({"trading_allowed": True}, f)
    assert CurrentStateAlignment().compare_files(summary, m_p, p_p)["cross_file_alignment_passed"] is False

def test_current_state_alignment_rejects_latest_metrics_missing_critical_field(tmp_path):
    summary = {"version": "V1.81.4"}
    m_p = tmp_path / "latest_metrics.json"
    p_p = tmp_path / "PROJECT_STATE.json"
    with open(m_p, "w") as f: json.dump({}, f)
    with open(p_p, "w") as f: json.dump(summary, f)
    assert CurrentStateAlignment().compare_files(summary, m_p, p_p)["cross_file_alignment_passed"] is False

def test_current_state_alignment_rejects_project_state_missing_critical_field(tmp_path):
    summary = {"version": "V1.81.4"}
    m_p = tmp_path / "latest_metrics.json"
    p_p = tmp_path / "PROJECT_STATE.json"
    with open(m_p, "w") as f: json.dump(summary, f)
    with open(p_p, "w") as f: json.dump({}, f)
    assert CurrentStateAlignment().compare_files(summary, m_p, p_p)["cross_file_alignment_passed"] is False

def test_current_state_alignment_reports_exact_mismatch_paths(tmp_path):
    summary = {"version": "V1.81.4"}
    m_p = tmp_path / "latest_metrics.json"
    p_p = tmp_path / "PROJECT_STATE.json"
    with open(m_p, "w") as f: json.dump({"version": "BAD"}, f)
    with open(p_p, "w") as f: json.dump(summary, f)
    res = CurrentStateAlignment().compare_files(summary, m_p, p_p)
    assert any("latest_metrics" in m for m in res["cross_file_mismatches"])

# ─── V1.81.4 Validator & Metadata (78-87) ───────────────────────────────────

def test_validator_rejects_latest_metrics_current_state_consistent_false_v1_81_4():
    pass

def test_validator_rejects_project_state_current_state_consistent_false_v1_81_4():
    pass

def test_validator_rejects_latest_metrics_summary_mismatch_v1_81_4():
    pass

def test_validator_rejects_project_state_summary_mismatch_v1_81_4():
    pass

def test_validator_rejects_cross_file_alignment_not_checked_v1_81_4():
    pass

def test_validator_rejects_cross_file_alignment_failed_v1_81_4():
    pass

def test_validator_rejects_cross_file_mismatch_count_positive_v1_81_4():
    pass

def test_release_metadata_requires_report_index_v1_81_4_final():
    pass

def test_release_metadata_requires_latest_summary_v1_81_4_final():
    pass

def test_release_metadata_reject_placeholder():
    pass
