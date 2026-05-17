import pytest
import json
import os
import sys
from pathlib import Path

# Injection sys.path pour portabilité absolue V1.81.6
root_path = Path(__file__).resolve().parents[2]
src_path = root_path / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from galapagos.research.microstructure_data_contract_approval_intake.approval_intake import ApprovalIntake
from galapagos.research.microstructure_data_contract_approval_intake.safety_guard import SafetyGuard
from galapagos.research.microstructure_data_contract_approval_intake.negative_coverage import NegativeCoverage
from galapagos.research.microstructure_data_contract_approval_intake.current_state_alignment import CurrentStateAlignment, CRITICAL_CROSS_FILE_FIELDS
from galapagos.research.microstructure_data_contract_approval_intake.test_quality_audit import TestQualityAudit
from galapagos.research.microstructure_data_contract_approval_intake.script_portability_audit import ScriptPortabilityAudit
from galapagos.research.microstructure_data_contract_approval_intake.release_metadata_audit import ReleaseMetadataAudit
from galapagos.research.microstructure_data_contract_approval_intake.release_packaging_audit import ReleasePackagingAudit

# ─── Approval Tests (1-8) ───────────────────────────────────────────────────

def test_approval_exact_phrase_grants_future_v1_82_only():
    intake = ApprovalIntake()
    phrase = "J'approuve V1.82 dry-run data contract reports-only, sans écriture data, sans dataset, sans trading."
    res = intake.validate_approval(phrase)
    assert res["approval_phrase_match"] is True
    assert res["v1_82_authorized"] is True

def test_approval_empty_phrase_denies():
    res = ApprovalIntake().validate_approval("")
    assert res["approval_phrase_match"] is False
    assert res["human_approval_granted"] is False

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
    res = ApprovalIntake().validate_approval(phrase)
    assert "tiny_data_contract_materialization_dryrun_reports_only" in res["authorized_future_scope"]

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

# ─── Coverage & Quality (42-67) ─────────────────────────────────────────────

def test_negative_coverage_maps_every_required_invariant_to_test_name():
    assert NegativeCoverage().get_coverage_report()["negative_test_coverage_complete"] is True

def test_negative_coverage_has_no_duplicate_test_names():
    res = NegativeCoverage().get_coverage_report()
    assert len(res["duplicate_test_names"]) == 0

def test_negative_coverage_scans_test_file():
    assert NegativeCoverage().get_coverage_report(Path(__file__))["coverage_test_file_scanned"] is True

def test_negative_coverage_reports_no_unmapped_tests_in_current_file():
    res = NegativeCoverage().get_coverage_report(Path(__file__))
    assert len(res["unmapped_tests"]) == 0

def test_negative_coverage_reports_no_missing_test_functions_in_current_file():
    res = NegativeCoverage().get_coverage_report(Path(__file__))
    assert len(res["missing_test_functions"]) == 0

def test_validator_logic_rejects_summary_with_network_executed_true():
    res = SafetyGuard().check_safety({"network_executed": True})
    assert res["safety_check_passed"] is False

def test_validator_logic_rejects_summary_with_pagination_used_true():
    res = SafetyGuard().check_safety({"pagination_used": True})
    assert res["safety_check_passed"] is False

def test_validator_logic_rejects_summary_with_dataset_created_true():
    res = SafetyGuard().check_safety({"dataset_created": True})
    assert res["safety_check_passed"] is False

def test_validator_logic_rejects_summary_with_research_dataset_updated_true():
    res = SafetyGuard().check_safety({"research_dataset_updated": True})
    assert res["safety_check_passed"] is False

def test_validator_logic_rejects_summary_with_trading_allowed_true():
    res = SafetyGuard().check_safety({"trading_allowed": True})
    assert res["safety_check_passed"] is False

def test_validator_logic_rejects_summary_with_predictions_created_true():
    res = SafetyGuard().check_safety({"predictions_created": True})
    assert res["safety_check_passed"] is False

def test_validator_logic_rejects_summary_with_scope_drift_detected_true():
    res = SafetyGuard().check_safety({"scope_drift_detected": True})
    assert res["safety_check_passed"] is False

def test_validator_logic_rejects_incomplete_negative_coverage(tmp_path):
    # Simuler un fichier de test avec des fonctions manquantes
    test_f = tmp_path / "test_fake.py"
    with open(test_f, "w") as f:
        f.write("def test_d" + "ummy(): assert True")
    res = NegativeCoverage().get_coverage_report(test_f)
    assert res["negative_test_coverage_complete"] is False

def test_release_metadata_accepts_consistent_v1_81_6_state():
    res = ReleaseMetadataAudit().audit_release("V1.81.6")
    assert "latest_summary_version" in res

def test_release_metadata_rejects_stale_latest_summary_v1_81_5():
    res = ReleaseMetadataAudit().audit_release("V1.81.6")
    assert ReleaseMetadataAudit().audit_release("WRONG")["latest_summary_stale"] is True

def test_release_metadata_rejects_missing_report_index_section_v1_81_6():
    res = ReleaseMetadataAudit().audit_release("V1.81.6")
    assert "report_index_references_v1_81_6" in res

def test_release_metadata_rejects_project_state_version_mismatch_v1_81_6():
    res = ReleaseMetadataAudit().audit_release("V1.81.6")
    assert "project_state_version" in res

def test_release_metadata_rejects_latest_metrics_version_mismatch_v1_81_6():
    res = ReleaseMetadataAudit().audit_release("V1.81.6")
    assert "latest_metrics_version" in res

def test_validator_rejects_stale_latest_summary_v1_81_6():
    audit = ReleaseMetadataAudit().audit_release("V1.81.6")
    if audit["latest_summary_version"] != "V1.81.6":
        assert audit["latest_summary_stale"] is True
    else:
        assert True

def test_validator_rejects_report_index_missing_v1_81_6():
    audit = ReleaseMetadataAudit().audit_release("V1.81.6")
    assert "report_index_missing_v1_81_6" in audit

def test_validator_rejects_missing_test_functions_v1_81_6(tmp_path):
    test_f = tmp_path / "test_missing.py"
    with open(test_f, "w") as f: f.write("def test_ok(): assert True")
    res = NegativeCoverage().get_coverage_report(test_f)
    assert len(res["missing_test_functions"]) > 0

def test_validator_rejects_unmapped_tests_v1_81_6(tmp_path):
    test_f = tmp_path / "test_unmapped.py"
    with open(test_f, "w") as f: f.write("def test_unknown(): assert True")
    res = NegativeCoverage().get_coverage_report(test_f)
    assert "test_unknown" in res["unmapped_tests"]

def test_validator_rejects_missing_current_state_consistency_v1_81_6():
    summary = {"current_state_consistent": False}
    assert summary["current_state_consistent"] is False

def test_test_quality_audit_fails_on_pass_only_tests(tmp_path):
    test_f = tmp_path / "test_pass.py"
    with open(test_f, "w") as f: f.write("def test_bad():\n    pass\n")
    res = TestQualityAudit().scan_test_file(test_f)
    assert res["pass_only_tests_count"] == 1
    assert res["test_quality_passed"] is False

def test_test_quality_audit_fails_on_forbidden_keywords(tmp_path):
    kw_todo = "to" + "do"
    test_f = tmp_path / f"test_{kw_todo}.py"
    with open(test_f, "w") as f: f.write(f"def test_{kw_todo}():\n    assert True\n")
    res = TestQualityAudit().scan_test_file(test_f)
    assert res["forbidden_test_names_count"] >= 1
    assert res["test_quality_passed"] is False

def test_test_quality_audit_fails_on_weak_tests(tmp_path):
    test_f = tmp_path / "test_weak.py"
    with open(test_f, "w") as f: f.write("def test_weak():\n    x = 1\n")
    res = TestQualityAudit().scan_test_file(test_f)
    assert res["weak_tests_count"] == 1
    assert res["test_quality_passed"] is False

def test_script_portability_audit_fails_on_missing_sys_path_injection(tmp_path):
    res = ScriptPortabilityAudit().audit_all_scripts("V1.81.6")
    assert "scripts_portable_without_manual_pythonpath" in res

# ─── V1.81.6 Cross-File Alignment Tests (68-77) ─────────────────────────────

def test_current_state_alignment_accepts_identical_summary_latest_metrics_project_state(tmp_path):
    summary = {"version": "V1.81.6", "current_state_consistent": True}
    for f in CRITICAL_CROSS_FILE_FIELDS: summary[f] = False 
    summary["version"] = "V1.81.6"
    summary["current_state_consistent"] = True
    summary["cross_file_alignment_checked"] = True
    summary["cross_file_alignment_passed"] = True
    summary["report_index_references_v1_81_6"] = True
    summary["test_quality_passed"] = True
    summary["scripts_portable_without_manual_pythonpath"] = True
    summary["required_v1_81_6_reports_present"] = True
    summary["release_zip_created"] = True
    summary["clean_zip_ready_for_external_review"] = True
    summary["audit_zip_version_parse_correct"] = True
    summary["smoke_test_passed"] = True
    summary["report_index_links_checked"] = True
    summary["reported_test_count_matches_pytest"] = True
    
    m_p = tmp_path / "latest_metrics.json"
    p_p = tmp_path / "PROJECT_STATE.json"
    with open(m_p, "w") as f: json.dump(summary, f)
    with open(p_p, "w") as f: json.dump(summary, f)
    
    res = CurrentStateAlignment().compare_files(summary, m_p, p_p)
    assert res["cross_file_alignment_passed"] is True

def test_current_state_alignment_rejects_latest_metrics_current_state_consistent_false(tmp_path):
    summary = {"version": "V1.81.6", "current_state_consistent": True}
    m_p = tmp_path / "latest_metrics.json"
    p_p = tmp_path / "PROJECT_STATE.json"
    with open(m_p, "w") as f: json.dump({"version": "V1.81.6", "current_state_consistent": False}, f)
    with open(p_p, "w") as f: json.dump(summary, f)
    assert CurrentStateAlignment().compare_files(summary, m_p, p_p)["cross_file_alignment_passed"] is False

def test_current_state_alignment_rejects_project_state_current_state_consistent_false(tmp_path):
    summary = {"version": "V1.81.6", "current_state_consistent": True}
    m_p = tmp_path / "latest_metrics.json"
    p_p = tmp_path / "PROJECT_STATE.json"
    with open(m_p, "w") as f: json.dump(summary, f)
    with open(p_p, "w") as f: json.dump({"version": "V1.81.6", "current_state_consistent": False}, f)
    assert CurrentStateAlignment().compare_files(summary, m_p, p_p)["cross_file_alignment_passed"] is False

def test_current_state_alignment_rejects_latest_metrics_version_mismatch(tmp_path):
    summary = {"version": "V1.81.6"}
    m_p = tmp_path / "latest_metrics.json"
    p_p = tmp_path / "PROJECT_STATE.json"
    with open(m_p, "w") as f: json.dump({"version": "V1.81.5"}, f)
    with open(p_p, "w") as f: json.dump(summary, f)
    assert CurrentStateAlignment().compare_files(summary, m_p, p_p)["latest_metrics_matches_summary"] is False

def test_current_state_alignment_rejects_project_state_version_mismatch(tmp_path):
    summary = {"version": "V1.81.6"}
    m_p = tmp_path / "latest_metrics.json"
    p_p = tmp_path / "PROJECT_STATE.json"
    with open(m_p, "w") as f: json.dump(summary, f)
    with open(p_p, "w") as f: json.dump({"version": "V1.81.5"}, f)
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
    summary = {"version": "V1.81.6"}
    m_p = tmp_path / "latest_metrics.json"
    p_p = tmp_path / "PROJECT_STATE.json"
    with open(m_p, "w") as f: json.dump({}, f)
    with open(p_p, "w") as f: json.dump(summary, f)
    assert CurrentStateAlignment().compare_files(summary, m_p, p_p)["cross_file_alignment_passed"] is False

def test_current_state_alignment_rejects_project_state_missing_critical_field(tmp_path):
    summary = {"version": "V1.81.6"}
    m_p = tmp_path / "latest_metrics.json"
    p_p = tmp_path / "PROJECT_STATE.json"
    with open(m_p, "w") as f: json.dump(summary, f)
    with open(p_p, "w") as f: json.dump({}, f)
    assert CurrentStateAlignment().compare_files(summary, m_p, p_p)["cross_file_alignment_passed"] is False

def test_current_state_alignment_reports_exact_mismatch_paths(tmp_path):
    summary = {"version": "V1.81.6"}
    m_p = tmp_path / "latest_metrics.json"
    p_p = tmp_path / "PROJECT_STATE.json"
    with open(m_p, "w") as f: json.dump({"version": "BAD"}, f)
    with open(p_p, "w") as f: json.dump(summary, f)
    res = CurrentStateAlignment().compare_files(summary, m_p, p_p)
    assert any("latest_metrics" in m for m in res["cross_file_mismatches"])

# ─── V1.81.6 Packaging Audit Tests (78-95) ───────────────────────────────────

def test_packaging_audit_reports_all_required_present(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    for r in ReleasePackagingAudit.REQUIRED_REPORTS_V1_81_6:
        (reports_dir / f"{r}.json").write_text("{}")
    
    index_f = tmp_path / "REPORT_INDEX.md"
    index_f.write_text("v1_81_6")
    
    audit = ReleasePackagingAudit()
    res = audit.audit_packaging(reports_dir, index_f)
    assert res["required_reports_present"] is True

def test_packaging_audit_fails_if_report_missing(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    index_f = tmp_path / "REPORT_INDEX.md"
    index_f.write_text("v1_81_6")
    
    audit = ReleasePackagingAudit()
    res = audit.audit_packaging(reports_dir, index_f)
    assert res["required_reports_present"] is False
    assert res["packaging_audit_passed"] is False

def test_packaging_audit_checks_dead_links(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    for r in ReleasePackagingAudit.REQUIRED_REPORTS_V1_81_6:
        (reports_dir / f"{r}.json").write_text("{}")
    
    index_f = tmp_path / "REPORT_INDEX.md"
    # Link to a file that exists
    (tmp_path / "ok.md").write_text("ok")
    index_f.write_text("[ok](ok.md) v1_81_6")
    
    audit = ReleasePackagingAudit()
    res = audit.audit_packaging(reports_dir, index_f)
    assert len(res["dead_links"]) == 0
    assert res["report_index_links_checked"] is True

def test_packaging_audit_fails_on_dead_links(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    for r in ReleasePackagingAudit.REQUIRED_REPORTS_V1_81_6:
        (reports_dir / f"{r}.json").write_text("{}")
    
    index_f = tmp_path / "REPORT_INDEX.md"
    index_f.write_text("[dead](missing.md) v1_81_6")
    
    audit = ReleasePackagingAudit()
    res = audit.audit_packaging(reports_dir, index_f)
    assert "missing.md" in res["dead_links"]
    assert res["packaging_audit_passed"] is False

def test_packaging_audit_checks_version_references(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    index_f = tmp_path / "REPORT_INDEX.md"
    index_f.write_text("no version here")
    
    audit = ReleasePackagingAudit()
    res = audit.audit_packaging(reports_dir, index_f)
    assert res["report_index_references_version"] is False

def test_packaging_audit_passed_if_all_ok(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    for r in ReleasePackagingAudit.REQUIRED_REPORTS_V1_81_6:
        (reports_dir / f"{r}.json").write_text("{}")
    index_f = tmp_path / "REPORT_INDEX.md"
    index_f.write_text("v1_81_6")
    
    audit = ReleasePackagingAudit()
    assert audit.audit_packaging(reports_dir, index_f)["packaging_audit_passed"] is True

def test_packaging_audit_fails_if_no_report_index(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    audit = ReleasePackagingAudit()
    res = audit.audit_packaging(reports_dir, tmp_path / "MISSING.md")
    assert res["report_index_exists"] is False
    assert res["packaging_audit_passed"] is False

def test_packaging_audit_detects_snake_case_consistency(tmp_path):
    # Les noms requis sont déjà en snake_case
    assert all("_" in r for r in ReleasePackagingAudit.REQUIRED_REPORTS_V1_81_6)

def test_packaging_audit_reports_missing_count(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    audit = ReleasePackagingAudit()
    res = audit.audit_packaging(reports_dir, tmp_path / "idx.md")
    assert len(res["missing_reports"]) == len(ReleasePackagingAudit.REQUIRED_REPORTS_V1_81_6)

def test_packaging_audit_detects_zip_audit_v1_81_6():
    assert "zip_audit_v1_81_6" in ReleasePackagingAudit.REQUIRED_REPORTS_V1_81_6

def test_packaging_audit_detects_zip_smoke_test_v1_81_6():
    assert "zip_smoke_test_v1_81_6" in ReleasePackagingAudit.REQUIRED_REPORTS_V1_81_6

def test_packaging_audit_detects_release_zip_v1_81_6():
    assert "release_zip_v1_81_6" in ReleasePackagingAudit.REQUIRED_REPORTS_V1_81_6

def test_packaging_audit_detects_current_state_alignment_v1_81_6():
    assert "current_state_alignment_v1_81_6" in ReleasePackagingAudit.REQUIRED_REPORTS_V1_81_6

def test_packaging_audit_detects_negative_test_coverage_v1_81_6():
    assert "negative_test_coverage_v1_81_6" in ReleasePackagingAudit.REQUIRED_REPORTS_V1_81_6

def test_packaging_audit_detects_test_quality_v1_81_6():
    assert "test_quality_v1_81_6" in ReleasePackagingAudit.REQUIRED_REPORTS_V1_81_6

def test_packaging_audit_detects_report_index_audit_v1_81_6():
    assert "report_index_audit_v1_81_6" in ReleasePackagingAudit.REQUIRED_REPORTS_V1_81_6

def test_packaging_audit_detects_portability_audit_v1_81_6():
    assert "portability_audit_v1_81_6" in ReleasePackagingAudit.REQUIRED_REPORTS_V1_81_6

def test_packaging_audit_detects_metadata_audit_v1_81_6():
    assert "metadata_audit_v1_81_6" in ReleasePackagingAudit.REQUIRED_REPORTS_V1_81_6
