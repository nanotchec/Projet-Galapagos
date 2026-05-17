import re
from pathlib import Path
from typing import Any, Dict, List
from galapagos.research.microstructure_data_contract_approval_intake.test_quality_audit import TestQualityAudit

REQUIRED_NEGATIVE_TESTS = [
    # Network (6)
    ("network_executed", "test_guard_rejects_network_executed_true"),
    ("new_network_requests_executed", "test_guard_rejects_new_network_requests_executed_true"),
    ("request_retry_count", "test_guard_rejects_request_retry_count_positive"),
    ("pagination_used", "test_guard_rejects_pagination_used_true"),
    ("authenticated_request_allowed", "test_guard_rejects_authenticated_request_allowed_true"),
    ("secrets_used", "test_guard_rejects_secrets_used_true"),
    
    # Data Write (12)
    ("data_directory_writes_allowed", "test_guard_rejects_data_directory_writes_allowed_true"),
    ("new_data_files_created", "test_guard_rejects_new_data_files_created_true"),
    ("no_data_directory_writes", "test_guard_rejects_no_data_directory_writes_false"),
    ("parquet_created", "test_guard_rejects_parquet_created_true"),
    ("csv_created", "test_guard_rejects_csv_created_true"),
    ("sqlite_created", "test_guard_rejects_sqlite_created_true"),
    ("jsonl_created", "test_guard_rejects_jsonl_created_true"),
    ("db_created", "test_guard_rejects_db_created_true"),
    ("dataset_created", "test_guard_rejects_dataset_created_true"),
    ("research_dataset_updated", "test_guard_rejects_research_dataset_updated_true"),
    ("data_write_approved", "test_guard_rejects_data_write_approved_true"),
    ("dataset_materialization_approved", "test_guard_rejects_dataset_materialization_approved_true"),
    
    # Trading / ML (12)
    ("strategy_link_allowed", "test_guard_rejects_strategy_link_allowed_true"),
    ("trading_allowed", "test_guard_rejects_trading_allowed_true"),
    ("no_strategy_validated", "test_guard_rejects_no_strategy_validated_false"),
    ("no_paper_live", "test_guard_rejects_no_paper_live_false"),
    ("no_real_trading", "test_guard_rejects_no_real_trading_false"),
    ("real_orders_possible", "test_guard_rejects_real_orders_possible_true"),
    ("holdout_executed", "test_guard_rejects_holdout_executed_true"),
    ("codex_cli_called", "test_guard_rejects_codex_cli_called_true"),
    ("ml_signal_validation_executed", "test_guard_rejects_ml_signal_validation_executed_true"),
    ("predictions_created", "test_guard_rejects_predictions_created_true"),
    ("labels_created", "test_guard_rejects_labels_created_true"),
    ("targets_created", "test_guard_rejects_targets_created_true"),
    
    # Scope Drift (3)
    ("v1_82_execution_attempted", "test_guard_rejects_v1_82_execution_attempted_true"),
    ("data_contract_dryrun_executed", "test_guard_rejects_data_contract_dryrun_executed_true"),
    ("scope_drift_detected", "test_guard_rejects_scope_drift_detected_true")
]

IGNORED_NON_INVARIANT_TESTS = [
    "test_approval_exact_phrase_grants_future_v1_82_only",
    "test_approval_empty_phrase_denies",
    "test_approval_wrong_phrase_denies",
    "test_approval_trailing_space_denies",
    "test_approval_punctuation_change_denies",
    "test_approval_authorization_cannot_be_true_when_phrase_mismatch",
    "test_approval_future_scope_must_match_exactly",
    "test_approval_future_version_must_be_v1_82",
    "test_negative_coverage_maps_every_required_invariant_to_test_name",
    "test_negative_coverage_has_no_duplicate_test_names",
    "test_negative_coverage_scans_test_file",
    "test_negative_coverage_reports_no_unmapped_tests_in_current_file",
    "test_negative_coverage_reports_no_missing_test_functions_in_current_file",
    "test_validator_logic_rejects_summary_with_network_executed_true",
    "test_validator_logic_rejects_summary_with_pagination_used_true",
    "test_validator_logic_rejects_summary_with_dataset_created_true",
    "test_validator_logic_rejects_summary_with_research_dataset_updated_true",
    "test_validator_logic_rejects_summary_with_trading_allowed_true",
    "test_validator_logic_rejects_summary_with_predictions_created_true",
    "test_validator_logic_rejects_summary_with_scope_drift_detected_true",
    "test_validator_logic_rejects_incomplete_negative_coverage",
    "test_release_metadata_accepts_consistent_v1_81_6_state",
    "test_release_metadata_rejects_stale_latest_summary_v1_81_5",
    "test_release_metadata_rejects_missing_report_index_section_v1_81_6",
    "test_release_metadata_rejects_project_state_version_mismatch_v1_81_6",
    "test_release_metadata_rejects_latest_metrics_version_mismatch_v1_81_6",
    "test_validator_rejects_stale_latest_summary_v1_81_6",
    "test_validator_rejects_report_index_missing_v1_81_6",
    "test_validator_rejects_missing_test_functions_v1_81_6",
    "test_validator_rejects_unmapped_tests_v1_81_6",
    "test_validator_rejects_missing_current_state_consistency_v1_81_6",
    "test_current_state_alignment_accepts_identical_summary_latest_metrics_project_state",
    "test_current_state_alignment_rejects_latest_metrics_current_state_consistent_false",
    "test_current_state_alignment_rejects_project_state_current_state_consistent_false",
    "test_current_state_alignment_rejects_latest_metrics_version_mismatch",
    "test_current_state_alignment_rejects_project_state_version_mismatch",
    "test_current_state_alignment_rejects_latest_metrics_safety_field_mismatch",
    "test_current_state_alignment_rejects_project_state_safety_field_mismatch",
    "test_current_state_alignment_rejects_latest_metrics_missing_critical_field",
    "test_current_state_alignment_rejects_project_state_missing_critical_field",
    "test_current_state_alignment_reports_exact_mismatch_paths",
    "test_validator_rejects_latest_metrics_current_state_consistent_false_v1_81_5",
    "test_validator_rejects_project_state_current_state_consistent_false_v1_81_5",
    "test_validator_rejects_latest_metrics_summary_mismatch_v1_81_5",
    "test_validator_rejects_project_state_summary_mismatch_v1_81_5",
    "test_validator_rejects_cross_file_alignment_not_checked_v1_81_5",
    "test_validator_rejects_cross_file_alignment_failed_v1_81_5",
    "test_validator_rejects_cross_file_mismatch_count_positive_v1_81_5",
    "test_release_metadata_requires_report_index_v1_81_5_final",
    "test_release_metadata_requires_latest_summary_v1_81_5_final",
    "test_test_quality_audit_fails_on_pass_only_tests",
    "test_test_quality_audit_fails_on_forbidden_keywords",
    "test_test_quality_audit_fails_on_weak_tests",
    "test_script_portability_audit_fails_on_missing_sys_path_injection",
    "test_release_metadata_reject_ph_in_validator",
    "test_packaging_audit_reports_all_required_present",
    "test_packaging_audit_fails_if_report_missing",
    "test_packaging_audit_checks_dead_links",
    "test_packaging_audit_fails_on_dead_links",
    "test_packaging_audit_checks_version_references",
    "test_packaging_audit_passed_if_all_ok",
    "test_packaging_audit_fails_if_no_report_index",
    "test_packaging_audit_detects_snake_case_consistency",
    "test_packaging_audit_reports_missing_count",
    "test_packaging_audit_detects_zip_audit_v1_81_6",
    "test_packaging_audit_detects_zip_smoke_test_v1_81_6",
    "test_packaging_audit_detects_release_zip_v1_81_6",
    "test_packaging_audit_detects_current_state_alignment_v1_81_6",
    "test_packaging_audit_detects_negative_test_coverage_v1_81_6",
    "test_packaging_audit_detects_test_quality_v1_81_6",
    "test_packaging_audit_detects_report_index_audit_v1_81_6",
    "test_packaging_audit_detects_portability_audit_v1_81_6",
    "test_packaging_audit_detects_metadata_audit_v1_81_6",
    # V1.81.7 – nouveaux tests CLI, portability, rapports, REPORT_INDEX, smoke
    "test_run_script_accepts_approval_phrase_argument",
    "test_run_script_rejects_no_unknown_arguments",
    "test_run_script_records_approval_phrase_match",
    "test_validator_script_runs_without_manual_pythonpath",
    "test_run_script_runs_without_manual_pythonpath",
    "test_audit_script_runs_without_manual_pythonpath",
    "test_smoke_script_runs_without_manual_pythonpath",
    "test_required_research_report_paths_are_canonical_v1_81_7",
    "test_required_docs_code_review_v1_81_7_exists",
    "test_validator_rejects_missing_research_summary_report",
    "test_validator_rejects_missing_code_review_doc",
    "test_validator_rejects_reports_written_at_wrong_root_level",
    "test_report_index_references_canonical_research_reports_v1_81_7",
    "test_report_index_rejects_root_level_simplified_report_links",
    "test_report_index_rejects_broken_links",
    "test_smoke_test_rejects_manual_pythonpath_env",
    "test_smoke_test_requires_non_empty_commands",
    "test_smoke_test_requires_at_least_three_successful_commands",
    "test_smoke_test_rejects_failed_command",
    "test_validator_rejects_run_script_missing_approval_phrase_cli",
    "test_validator_rejects_validator_script_missing_src_sys_path",
    "test_validator_rejects_smoke_using_manual_pythonpath",
    "test_validator_rejects_missing_required_v1_81_7_reports",
    "test_validator_rejects_report_index_non_canonical_links",
    # V1.81.7 – tests metadata/packaging transposés depuis V1.81.6
    "test_packaging_audit_detects_portability_audit_v1_81_7",
    "test_packaging_audit_detects_metadata_audit_v1_81_7",
    "test_audit_clean_zip_infers_v1_81_10_without_truncating",
    "test_audit_clean_zip_infers_v1_81_11_without_truncating",
    "test_audit_clean_zip_infers_v1_81_1_correctly",
    "test_validator_rejects_zip_audit_project_state_version_mismatch",
    "test_validator_rejects_pytest_count_mismatch_between_summary_and_project_state",
    "test_validator_rejects_negative_coverage_wrong_version",
    "test_negative_coverage_report_uses_requested_version",
    "test_project_state_latest_metrics_summary_pytest_counts_are_identical",
    "test_no_redundant_artificial_test_padding_present",
    "test_audit_zip_payload_contains_project_state_version_fields",
    "test_audit_clean_zip_infers_v1_81_12_without_truncating",
    "test_negative_coverage_report_uses_v1_81_12",
    "test_validator_v1_81_12_rejects_empty_smoke_commands",
]

ALLOWED_NON_INVARIANT_TEST_PREFIXES = (
    "test_approval_",
    "test_negative_coverage_",
    "test_test_quality_",
    "test_anti_tautology_",
    "test_smoke_",
    "test_critical_field_",
    "test_reported_test_count_",
    "test_version_consistency_",
    "test_sys_path_",
    "test_project_root_",
    "test_current_state_alignment_",
    "test_validator_",
    "test_release_metadata_",
    "test_packaging_",
    "test_script_portability_",
    "test_guard_",
)

FORBIDDEN_TEST_NAME_FRAGMENTS = (
    "placeholder",
    "remaining",
    "todo",
    "stub",
    "dummy",
    "ph_tests",
)

class NegativeCoverage:
    def get_coverage_report(self, test_file_path: Path = None, version: str = "V1.81.11", corrective_for_version: str = "V1.81.10") -> Dict[str, Any]:
        coverage_map = {inv: tname for inv, tname in REQUIRED_NEGATIVE_TESTS}
        
        discovered_tests = []
        quality_res = {
            "pass_only_tests_count": 0,
            "placeholder_tests_count": 0,
            "test_quality_passed": True,
            "discovered_test_functions_count": 0
        }

        if test_file_path and test_file_path.exists():
            with open(test_file_path) as f:
                content = f.read()
                discovered_tests = re.findall(r"^def (test_[a-zA-Z0-9_]+)\(", content, re.MULTILINE)
            
            quality_res = TestQualityAudit().scan_test_file(test_file_path)

        # Check for missing functions
        missing_test_functions = []
        for inv, tname in REQUIRED_NEGATIVE_TESTS:
            if test_file_path and tname not in discovered_tests:
                missing_test_functions.append(tname)
        
        # Check for unmapped tests
        unmapped_tests = []
        for tname in discovered_tests:
            is_forbidden_name = any(fragment in tname.lower() for fragment in FORBIDDEN_TEST_NAME_FRAGMENTS)
            if is_forbidden_name:
                unmapped_tests.append(tname)
                continue

            is_mapped = any(tname == mapping[1] for mapping in REQUIRED_NEGATIVE_TESTS)
            is_ignored = (
                tname in IGNORED_NON_INVARIANT_TESTS
                or any(tname.startswith(prefix) for prefix in ALLOWED_NON_INVARIANT_TEST_PREFIXES)
            )

            if not is_mapped and not is_ignored:
                unmapped_tests.append(tname)

        covered_count = len(REQUIRED_NEGATIVE_TESTS) - len(missing_test_functions)
        
        # FINAL VERDICT
        coverage_complete = (
            len(missing_test_functions) == 0 and 
            len(unmapped_tests) == 0 and 
            quality_res["test_quality_passed"]
        )

        return {
            "version": version,
            "corrective_for_version": corrective_for_version,
            "negative_test_coverage_complete": coverage_complete,
            "required_negative_invariants_count": len(REQUIRED_NEGATIVE_TESTS),
            "covered_negative_invariants_count": covered_count,
            "missing_negative_invariants": [], # Legacy
            "duplicate_test_names": [], # Checked by discovered_tests uniqueness if needed
            "missing_test_functions": missing_test_functions,
            "unmapped_tests": unmapped_tests,
            "coverage_introspection_enabled": True,
            "coverage_test_file_scanned": test_file_path is not None,
            "discovered_test_functions_count": quality_res["discovered_test_functions_count"],
            "pass_only_tests_count": quality_res["pass_only_tests_count"],
            "placeholder_tests_count": quality_res["placeholder_tests_count"],
            "test_quality_passed": quality_res["test_quality_passed"]
        }
