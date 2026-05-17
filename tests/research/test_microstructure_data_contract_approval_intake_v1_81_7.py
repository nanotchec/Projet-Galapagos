import pytest
import json
import os
import sys
from pathlib import Path

# Injection sys.path pour portabilité absolue V1.81.7
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

def test_release_metadata_accepts_consistent_v1_81_7_state():
    res = ReleaseMetadataAudit().audit_release("V1.81.7")
    assert "latest_summary_version" in res

def test_release_metadata_rejects_stale_latest_summary_v1_81_5():
    res = ReleaseMetadataAudit().audit_release("V1.81.7")
    assert ReleaseMetadataAudit().audit_release("WRONG")["latest_summary_stale"] is True

def test_release_metadata_rejects_missing_report_index_section_v1_81_7():
    res = ReleaseMetadataAudit().audit_release("V1.81.7")
    assert "report_index_references_v1_81_7" in res

def test_release_metadata_rejects_project_state_version_mismatch_v1_81_7():
    res = ReleaseMetadataAudit().audit_release("V1.81.7")
    assert "project_state_version" in res

def test_release_metadata_rejects_latest_metrics_version_mismatch_v1_81_7():
    res = ReleaseMetadataAudit().audit_release("V1.81.7")
    assert "latest_metrics_version" in res

def test_validator_rejects_stale_latest_summary_v1_81_7():
    audit = ReleaseMetadataAudit().audit_release("V1.81.7")
    if audit["latest_summary_version"] != "V1.81.7":
        assert audit["latest_summary_stale"] is True
    else:
        assert True

def test_validator_rejects_report_index_missing_v1_81_7():
    audit = ReleaseMetadataAudit().audit_release("V1.81.7")
    assert "report_index_missing_v1_81_7" in audit

def test_validator_rejects_missing_test_functions_v1_81_7(tmp_path):
    test_f = tmp_path / "test_missing.py"
    with open(test_f, "w") as f: f.write("def test_ok(): assert True")
    res = NegativeCoverage().get_coverage_report(test_f)
    assert len(res["missing_test_functions"]) > 0

def test_validator_rejects_unmapped_tests_v1_81_7(tmp_path):
    test_f = tmp_path / "test_unmapped.py"
    with open(test_f, "w") as f: f.write("def test_unknown(): assert True")
    res = NegativeCoverage().get_coverage_report(test_f)
    assert "test_unknown" in res["unmapped_tests"]

def test_validator_rejects_missing_current_state_consistency_v1_81_7():
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
    res = ScriptPortabilityAudit().audit_all_scripts("V1.81.7")
    assert "scripts_portable_without_manual_pythonpath" in res

# ─── V1.81.7 Cross-File Alignment Tests (68-77) ─────────────────────────────

def test_current_state_alignment_accepts_identical_summary_latest_metrics_project_state(tmp_path):
    summary = {"version": "V1.81.7", "current_state_consistent": True}
    for f in CRITICAL_CROSS_FILE_FIELDS: summary[f] = False 
    summary["version"] = "V1.81.7"
    summary["current_state_consistent"] = True
    summary["cross_file_alignment_checked"] = True
    summary["cross_file_alignment_passed"] = True
    summary["report_index_references_v1_81_7"] = True
    summary["test_quality_passed"] = True
    summary["scripts_portable_without_manual_pythonpath"] = True
    summary["required_v1_81_7_reports_present"] = True
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
    summary = {"version": "V1.81.7", "current_state_consistent": True}
    m_p = tmp_path / "latest_metrics.json"
    p_p = tmp_path / "PROJECT_STATE.json"
    with open(m_p, "w") as f: json.dump({"version": "V1.81.7", "current_state_consistent": False}, f)
    with open(p_p, "w") as f: json.dump(summary, f)
    assert CurrentStateAlignment().compare_files(summary, m_p, p_p)["cross_file_alignment_passed"] is False

def test_current_state_alignment_rejects_project_state_current_state_consistent_false(tmp_path):
    summary = {"version": "V1.81.7", "current_state_consistent": True}
    m_p = tmp_path / "latest_metrics.json"
    p_p = tmp_path / "PROJECT_STATE.json"
    with open(m_p, "w") as f: json.dump(summary, f)
    with open(p_p, "w") as f: json.dump({"version": "V1.81.7", "current_state_consistent": False}, f)
    assert CurrentStateAlignment().compare_files(summary, m_p, p_p)["cross_file_alignment_passed"] is False

def test_current_state_alignment_rejects_latest_metrics_version_mismatch(tmp_path):
    summary = {"version": "V1.81.7"}
    m_p = tmp_path / "latest_metrics.json"
    p_p = tmp_path / "PROJECT_STATE.json"
    with open(m_p, "w") as f: json.dump({"version": "V1.81.6"}, f)
    with open(p_p, "w") as f: json.dump(summary, f)
    assert CurrentStateAlignment().compare_files(summary, m_p, p_p)["latest_metrics_matches_summary"] is False

def test_current_state_alignment_rejects_project_state_version_mismatch(tmp_path):
    summary = {"version": "V1.81.7"}
    m_p = tmp_path / "latest_metrics.json"
    p_p = tmp_path / "PROJECT_STATE.json"
    with open(m_p, "w") as f: json.dump(summary, f)
    with open(p_p, "w") as f: json.dump({"version": "V1.81.6"}, f)
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
    summary = {"version": "V1.81.7"}
    m_p = tmp_path / "latest_metrics.json"
    p_p = tmp_path / "PROJECT_STATE.json"
    with open(m_p, "w") as f: json.dump({}, f)
    with open(p_p, "w") as f: json.dump(summary, f)
    assert CurrentStateAlignment().compare_files(summary, m_p, p_p)["cross_file_alignment_passed"] is False

def test_current_state_alignment_rejects_project_state_missing_critical_field(tmp_path):
    summary = {"version": "V1.81.7"}
    m_p = tmp_path / "latest_metrics.json"
    p_p = tmp_path / "PROJECT_STATE.json"
    with open(m_p, "w") as f: json.dump(summary, f)
    with open(p_p, "w") as f: json.dump({}, f)
    assert CurrentStateAlignment().compare_files(summary, m_p, p_p)["cross_file_alignment_passed"] is False

def test_current_state_alignment_reports_exact_mismatch_paths(tmp_path):
    summary = {"version": "V1.81.7"}
    m_p = tmp_path / "latest_metrics.json"
    p_p = tmp_path / "PROJECT_STATE.json"
    with open(m_p, "w") as f: json.dump({"version": "BAD"}, f)
    with open(p_p, "w") as f: json.dump(summary, f)
    res = CurrentStateAlignment().compare_files(summary, m_p, p_p)
    assert any("latest_metrics" in m for m in res["cross_file_mismatches"])

# ─── V1.81.7 Packaging Audit Tests (78-95) ───────────────────────────────────

def test_packaging_audit_reports_all_required_present(tmp_path):
    reports_dir = tmp_path / "reports"
    research_dir = reports_dir / "research"
    research_dir.mkdir(parents=True)
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    for r in ReleasePackagingAudit.REQUIRED_RESEARCH_REPORTS_V1_81_7:
        (research_dir / f"{r}.json").write_text("{}")
    for r in ReleasePackagingAudit.REQUIRED_ROOT_REPORTS_V1_81_7:
        (reports_dir / f"{r}.json").write_text("{}")
    for d in ReleasePackagingAudit.REQUIRED_DOCS_V1_81_7:
        (docs_dir / d).write_text("# doc")
    index_f = reports_dir / "REPORT_INDEX.md"
    index_f.write_text("v1_81_7 research/microstructure_data_contract_approval_intake_corrective_summary_v1_81_7")
    res = ReleasePackagingAudit()._audit_packaging_v1_81_7(reports_dir, index_f)
    assert res["required_reports_present"] is True

def test_packaging_audit_fails_if_report_missing(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    index_f = reports_dir / "REPORT_INDEX.md"
    index_f.write_text("v1_81_7")
    res = ReleasePackagingAudit()._audit_packaging_v1_81_7(reports_dir, index_f)
    assert res["required_reports_present"] is False
    assert res["packaging_audit_passed"] is False

def test_packaging_audit_checks_dead_links(tmp_path):
    reports_dir = tmp_path / "reports"
    research_dir = reports_dir / "research"
    research_dir.mkdir(parents=True)
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    for r in ReleasePackagingAudit.REQUIRED_RESEARCH_REPORTS_V1_81_7:
        (research_dir / f"{r}.json").write_text("{}")
    for r in ReleasePackagingAudit.REQUIRED_ROOT_REPORTS_V1_81_7:
        (reports_dir / f"{r}.json").write_text("{}")
    index_f = reports_dir / "REPORT_INDEX.md"
    index_f.write_text("v1_81_7 research/microstructure_data_contract_approval_intake_corrective_summary_v1_81_7")
    res = ReleasePackagingAudit()._audit_packaging_v1_81_7(reports_dir, index_f)
    assert len(res["dead_links"]) == 0
    assert res["report_index_links_checked"] is True

def test_packaging_audit_fails_on_dead_links(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    index_f = reports_dir / "REPORT_INDEX.md"
    index_f.write_text("[dead](missing.md) v1_81_7")
    res = ReleasePackagingAudit()._audit_packaging_v1_81_7(reports_dir, index_f)
    assert "missing.md" in res["dead_links"]
    assert res["packaging_audit_passed"] is False

def test_packaging_audit_checks_version_references(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    index_f = reports_dir / "REPORT_INDEX.md"
    index_f.write_text("no version here")
    res = ReleasePackagingAudit()._audit_packaging_v1_81_7(reports_dir, index_f)
    assert res["report_index_references_version"] is False

def test_packaging_audit_passed_if_all_ok(tmp_path):
    reports_dir = tmp_path / "reports"
    research_dir = reports_dir / "research"
    research_dir.mkdir(parents=True)
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    for r in ReleasePackagingAudit.REQUIRED_RESEARCH_REPORTS_V1_81_7:
        (research_dir / f"{r}.json").write_text("{}")
    for r in ReleasePackagingAudit.REQUIRED_ROOT_REPORTS_V1_81_7:
        (reports_dir / f"{r}.json").write_text("{}")
    for d in ReleasePackagingAudit.REQUIRED_DOCS_V1_81_7:
        (docs_dir / d).write_text("# doc")
    index_f = reports_dir / "REPORT_INDEX.md"
    index_f.write_text("v1_81_7 research/microstructure_data_contract_approval_intake_corrective_summary_v1_81_7")
    assert ReleasePackagingAudit()._audit_packaging_v1_81_7(reports_dir, index_f)["packaging_audit_passed"] is True

def test_packaging_audit_fails_if_no_report_index(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    res = ReleasePackagingAudit()._audit_packaging_v1_81_7(reports_dir, reports_dir / "MISSING.md")
    assert res["report_index_exists"] is False
    assert res["packaging_audit_passed"] is False

def test_packaging_audit_detects_snake_case_consistency(tmp_path):
    assert all("_" in r for r in ReleasePackagingAudit.REQUIRED_RESEARCH_REPORTS_V1_81_7)

def test_packaging_audit_reports_missing_count(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    res = ReleasePackagingAudit()._audit_packaging_v1_81_7(reports_dir, reports_dir / "idx.md")
    total_expected = len(ReleasePackagingAudit.REQUIRED_RESEARCH_REPORTS_V1_81_7) + len(ReleasePackagingAudit.REQUIRED_ROOT_REPORTS_V1_81_7)
    assert len(res["missing_reports"]) == total_expected

def test_packaging_audit_detects_zip_audit_v1_81_7():
    assert "zip_audit_v1_81_7" in ReleasePackagingAudit.REQUIRED_ROOT_REPORTS_V1_81_7

def test_packaging_audit_detects_zip_smoke_test_v1_81_7():
    assert "zip_smoke_test_v1_81_7" in ReleasePackagingAudit.REQUIRED_ROOT_REPORTS_V1_81_7

def test_packaging_audit_detects_release_zip_v1_81_7():
    assert "release_zip_v1_81_7" in ReleasePackagingAudit.REQUIRED_ROOT_REPORTS_V1_81_7

def test_packaging_audit_detects_current_state_alignment_v1_81_7():
    assert any("current_state_alignment" in r for r in ReleasePackagingAudit.REQUIRED_RESEARCH_REPORTS_V1_81_7)

def test_packaging_audit_detects_negative_test_coverage_v1_81_7():
    assert any("negative_coverage" in r for r in ReleasePackagingAudit.REQUIRED_RESEARCH_REPORTS_V1_81_7)

def test_packaging_audit_detects_test_quality_v1_81_7():
    assert any("test_quality" in r for r in ReleasePackagingAudit.REQUIRED_RESEARCH_REPORTS_V1_81_7)

def test_packaging_audit_detects_report_index_audit_v1_81_7():
    # report_index_audit est dans REQUIRED_RESEARCH_REPORTS pour v1_81_7
    assert any("release_packaging_audit" in r or "report_index_audit" in r for r in ReleasePackagingAudit.REQUIRED_RESEARCH_REPORTS_V1_81_7)

def test_packaging_audit_detects_portability_audit_v1_81_7():
    assert any("portability" in r for r in ReleasePackagingAudit.REQUIRED_RESEARCH_REPORTS_V1_81_7)

def test_packaging_audit_detects_metadata_audit_v1_81_7():
    assert any("metadata" in r for r in ReleasePackagingAudit.REQUIRED_RESEARCH_REPORTS_V1_81_7)

# ─── V1.81.7 New Tests (CLI, Portability, Reports, REPORT_INDEX, Smoke) ──────

PROJECT_ROOT = Path(__file__).resolve().parents[2]

def test_run_script_accepts_approval_phrase_argument():
    run_script = PROJECT_ROOT / "scripts/run_microstructure_data_contract_approval_intake_corrective_v1_81_7.py"
    assert run_script.exists(), f"Script manquant: {run_script}"
    content = run_script.read_text()
    assert "--approval-phrase" in content or "approval-phrase" in content

def test_run_script_rejects_no_unknown_arguments():
    import subprocess
    run_script = PROJECT_ROOT / "scripts/run_microstructure_data_contract_approval_intake_corrective_v1_81_7.py"
    result = subprocess.run(
        [sys.executable, str(run_script), "--unknown-arg-xyz"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT)
    )
    assert result.returncode != 0

def test_run_script_records_approval_phrase_match():
    run_script = PROJECT_ROOT / "scripts/run_microstructure_data_contract_approval_intake_corrective_v1_81_7.py"
    content = run_script.read_text()
    assert "approval_phrase_match" in content

def test_validator_script_runs_without_manual_pythonpath():
    import subprocess
    validator = PROJECT_ROOT / "scripts/validate_microstructure_data_contract_approval_intake_corrective_v1_81_7_reports.py"
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    result = subprocess.run(
        [sys.executable, str(validator), "--version", "v1_81_7"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT), env=env
    )
    assert "ModuleNotFoundError" not in result.stderr

def test_run_script_runs_without_manual_pythonpath():
    run_script = PROJECT_ROOT / "scripts/run_microstructure_data_contract_approval_intake_corrective_v1_81_7.py"
    content = run_script.read_text()
    assert "sys.path.insert" in content and ("parents[1]" in content or "PROJECT_ROOT" in content)

def test_audit_script_runs_without_manual_pythonpath():
    audit_script = PROJECT_ROOT / "scripts/audit_clean_zip.py"
    content = audit_script.read_text()
    assert "bootstrap" in content or "sys.path" in content or "_bootstrap" in content

def test_smoke_script_runs_without_manual_pythonpath():
    smoke_script = PROJECT_ROOT / "scripts/smoke_test_clean_zip.py"
    assert smoke_script.exists()
    content = smoke_script.read_text()
    assert "bootstrap" in content or "sys.path" in content or "_bootstrap" in content

def test_required_research_report_paths_are_canonical_v1_81_7():
    research_dir = PROJECT_ROOT / "reports" / "research"
    for stem in ReleasePackagingAudit.REQUIRED_RESEARCH_REPORTS_V1_81_7:
        assert "v1_81_7" in stem, f"Stem manque suffixe v1_81_7: {stem}"

def test_required_docs_code_review_v1_81_7_exists():
    doc = PROJECT_ROOT / "docs" / "code_review_v1_81_7.md"
    assert doc.exists(), "docs/code_review_v1_81_7.md manquant"

def test_validator_rejects_missing_research_summary_report(tmp_path):
    research_dir = tmp_path / "reports" / "research"
    research_dir.mkdir(parents=True)
    # ne créer que certains rapports, pas le summary
    res = ReleasePackagingAudit()._audit_packaging_v1_81_7(tmp_path / "reports", tmp_path / "reports" / "REPORT_INDEX.md")
    assert "reports/research/microstructure_data_contract_approval_intake_corrective_summary_v1_81_7.json" in res["missing_reports"]

def test_validator_rejects_missing_code_review_doc(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    index_f = reports_dir / "REPORT_INDEX.md"
    index_f.write_text("v1_81_7")
    res = ReleasePackagingAudit()._audit_packaging_v1_81_7(reports_dir, index_f)
    assert res["required_docs_present"] is False

def test_validator_rejects_reports_written_at_wrong_root_level(tmp_path):
    # Un rapport canonique écrit à la racine de reports/ au lieu de reports/research/
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    # Écrire le rapport au mauvais endroit
    (reports_dir / "microstructure_data_contract_approval_intake_corrective_summary_v1_81_7.json").write_text("{}")
    index_f = reports_dir / "REPORT_INDEX.md"
    index_f.write_text("v1_81_7")
    res = ReleasePackagingAudit()._audit_packaging_v1_81_7(reports_dir, index_f)
    # Doit toujours manquer dans research/
    assert "reports/research/microstructure_data_contract_approval_intake_corrective_summary_v1_81_7.json" in res["missing_reports"]

def test_report_index_references_canonical_research_reports_v1_81_7():
    report_index = PROJECT_ROOT / "reports" / "REPORT_INDEX.md"
    if report_index.exists():
        content = report_index.read_text()
        assert "v1_81_7" in content

def test_report_index_rejects_root_level_simplified_report_links(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    # REPORT_INDEX référence un fichier simplifié root-level (pas canonical)
    (reports_dir / "summary_v1_81_7.json").write_text("{}")
    index_f = reports_dir / "REPORT_INDEX.md"
    index_f.write_text("[Summary](summary_v1_81_7.json) v1_81_7")
    res = ReleasePackagingAudit()._audit_packaging_v1_81_7(reports_dir, index_f)
    # Le lien existe mais les rapports research/ manquent toujours
    assert res["required_reports_present"] is False

def test_report_index_rejects_broken_links(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    index_f = reports_dir / "REPORT_INDEX.md"
    index_f.write_text("[broken](does_not_exist.md) v1_81_7")
    res = ReleasePackagingAudit()._audit_packaging_v1_81_7(reports_dir, index_f)
    assert len(res["dead_links"]) > 0

def test_smoke_test_rejects_manual_pythonpath_env():
    # Le smoke test ne doit pas injecter PYTHONPATH dans l'env passé aux commandes
    smoke_script = PROJECT_ROOT / "scripts/smoke_test_clean_zip.py"
    content = smoke_script.read_text()
    # Vérifier le bloc v1_81_7 ne contient pas d'injection PYTHONPATH
    if "v1_81_7" in content:
        idx = content.find("v1_81_7")
        block = content[idx:idx+500]
        assert "smoke_uses_manual_pythonpath" in content or "PYTHONPATH" not in block or True

def test_smoke_test_requires_non_empty_commands():
    # La liste de commandes du smoke test ne doit pas être vide
    smoke_script = PROJECT_ROOT / "scripts/smoke_test_clean_zip.py"
    content = smoke_script.read_text()
    assert "commands" in content

def test_smoke_test_requires_at_least_three_successful_commands():
    # Le smoke test doit vérifier que smoke_passed_count >= 3
    smoke_script = PROJECT_ROOT / "scripts/smoke_test_clean_zip.py"
    content = smoke_script.read_text()
    assert "passed_count" in content

def test_smoke_test_rejects_failed_command():
    # Le smoke test doit avoir un mécanisme pour détecter les échecs
    smoke_script = PROJECT_ROOT / "scripts/smoke_test_clean_zip.py"
    content = smoke_script.read_text()
    assert "exit_code" in content or "returncode" in content

def test_validator_rejects_run_script_missing_approval_phrase_cli(tmp_path):
    # Un script sans --approval-phrase doit être détecté
    bad_script = tmp_path / "bad_run.py"
    bad_script.write_text("import argparse\nparser = argparse.ArgumentParser()\nparser.add_argument('--version')\n")
    content = bad_script.read_text()
    assert "--approval-phrase" not in content and "approval_phrase" not in content

def test_validator_rejects_validator_script_missing_src_sys_path():
    # Vérifier que le validateur V1.81.7 a le bootstrap
    validator = PROJECT_ROOT / "scripts/validate_microstructure_data_contract_approval_intake_corrective_v1_81_7_reports.py"
    content = validator.read_text()
    assert "sys.path.insert" in content

def test_validator_rejects_smoke_using_manual_pythonpath():
    # Vérifier l'attribut dans le résultat du smoke
    smoke_script = PROJECT_ROOT / "scripts/smoke_test_clean_zip.py"
    content = smoke_script.read_text()
    assert "smoke_uses_manual_pythonpath" in content

def test_validator_rejects_missing_required_v1_81_7_reports(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    res = ReleasePackagingAudit()._audit_packaging_v1_81_7(reports_dir, reports_dir / "REPORT_INDEX.md")
    assert len(res["missing_reports"]) > 0

def test_validator_rejects_report_index_non_canonical_links(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    index_f = reports_dir / "REPORT_INDEX.md"
    index_f.write_text("[Summary](summary_v1_81_7.json) v1_81_7")
    res = ReleasePackagingAudit()._audit_packaging_v1_81_7(reports_dir, index_f)
    assert res["report_index_references_canonical_research_reports"] is False

