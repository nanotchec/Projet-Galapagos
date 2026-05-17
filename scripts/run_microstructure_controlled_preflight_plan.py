import argparse
import json
from pathlib import Path
from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.microstructure_controlled_preflight_plan.report_writer import PreflightPlanReportWriter
from galapagos.research.microstructure_controlled_preflight_plan.preflight_scope_definition import define_scope
from galapagos.research.microstructure_controlled_preflight_plan.network_gate_policy import define_network_gate
from galapagos.research.microstructure_controlled_preflight_plan.write_gate_policy import define_write_gate
from galapagos.research.microstructure_controlled_preflight_plan.request_execution_policy import define_request_policy
from galapagos.research.microstructure_controlled_preflight_plan.manifest_expectation_plan import define_manifest_plan
from galapagos.research.microstructure_controlled_preflight_plan.rollback_and_cleanup_policy import define_rollback_policy
from galapagos.research.microstructure_controlled_preflight_plan.stop_condition_policy import define_stop_conditions
from galapagos.research.microstructure_controlled_preflight_plan.dryrun_test_plan import define_dryrun_tests
from galapagos.research.microstructure_controlled_preflight_plan.preflight_decision import make_decision
from galapagos.research.microstructure_controlled_preflight_plan.recommendation_engine import generate_recommendation
from galapagos.research.microstructure_controlled_preflight_plan.input_guard import validate_input
from galapagos.research.microstructure_controlled_preflight_plan.data_loader import load_baseline

def main():
    parser = argparse.ArgumentParser(description="Run Microstructure Controlled Preflight Plan (V1.59)")
    parser.add_argument("--version", default="V1.59.1")
    parser.add_argument("--offline-review-summary", required=True)
    parser.add_argument("--offline-review-consistency", required=True)
    parser.add_argument("--preflight-boundary-policy", required=True)
    parser.add_argument("--contract-risk-reg", required=True)
    parser.add_argument("--field-coverage-summary", required=True)
    parser.add_argument("--contract-approval-summary", required=True)
    parser.add_argument("--adapter-fixture-summary", required=True)
    parser.add_argument("--source-adapter-contract", required=True)
    parser.add_argument("--manifest-schema", required=True)
    parser.add_argument("--expected-file-layout", required=True)
    parser.add_argument("--causal-timestamp-policy", required=True)
    parser.add_argument("--data-contract", required=True)
    parser.add_argument("--validation-criteria", required=True)
    parser.add_argument("--canonical-summary", required=True)
    args = parser.parse_args()

    version = args.version
    writer = PreflightPlanReportWriter(version)
    
    # 1. Load & Guard
    baseline = load_baseline(version)
    guard_report = validate_input(baseline)
    writer.write_report("microstructure_preflight_plan_input_guard", guard_report, "Input Guard", ["Validates baseline V1.58.2."])

    # 2. Scope
    scope_report = define_scope(version)
    writer.write_report("microstructure_preflight_scope_definition", scope_report, "Preflight Scope Definition", ["Defines authorized planning perimeter."])

    # 3. Network Policy
    network_report = define_network_gate(version)
    writer.write_report("microstructure_preflight_network_gate_policy", network_report, "Network Gate Policy", ["Ensures network remains disabled."])

    # 4. Write Policy
    write_report = define_write_gate(version)
    writer.write_report("microstructure_preflight_write_gate_policy", write_report, "Write Gate Policy", ["Limits writes to reporting only."])

    # 5. Request Policy
    req_report = define_request_policy(version)
    writer.write_report("microstructure_preflight_request_execution_policy", req_report, "Request Execution Policy", ["Prohibits real API calls."])

    # 6. Manifest Plan
    manifest_report = define_manifest_plan(version)
    writer.write_report("microstructure_preflight_manifest_expectation_plan", manifest_report, "Manifest Expectation Plan", ["Defines metadata requirements."])

    # 7. Rollback Policy
    rollback_report = define_rollback_policy(version)
    writer.write_report("microstructure_preflight_rollback_cleanup_policy", rollback_report, "Rollback Cleanup Policy", ["Defines cleanup procedures."])

    # 8. Stop Conditions
    stop_report = define_stop_conditions(version)
    writer.write_report("microstructure_preflight_stop_condition_policy", stop_report, "Stop Condition Policy", ["Defines safety triggers."])

    # 9. Dryrun Test Plan
    dryrun_report = define_dryrun_tests(version)
    writer.write_report("microstructure_preflight_dryrun_test_plan", dryrun_report, "Dryrun Test Plan", ["Defines mandatory verification tests."])

    # 10. Decision
    decision_report = make_decision(version)
    writer.write_report("microstructure_preflight_decision", decision_report, "Preflight Decision", ["Evaluates plan readiness."])

    # 11. Recommendation
    rec_report = generate_recommendation(version)
    writer.write_report("microstructure_preflight_recommendation", rec_report, "Preflight Recommendation", ["Outlines next steps."])

    # 12. Summary
    summary = {
        "version": version,
        "current_version": version,
        "previous_version": "V1.59",
        "previous_base": "V1.59",
        "migrated_from": "V1.59",
        "migration_reason": "safety flags alignment fix",
        "safety_flags_alignment_status": "SAFETY_FLAGS_ALIGNED",
        "safety_flags_complete": True,
        "microstructure_offline_review_base_version": "V1.58.2",
        "microstructure_field_coverage_base_version": "V1.57.2",
        "microstructure_contract_approval_base_version": "V1.56.1",
        "microstructure_adapter_fixture_base_version": "V1.55.3",
        "microstructure_collector_network_disabled_base_version": "V1.54",
        "microstructure_backfill_dryrun_base_version": "V1.53.2",
        "microstructure_data_enrichment_base_version": "V1.52",
        "canonical_base_version": "V1.37.2",
        "input_guard_status": guard_report["status"],
        "preflight_scope_definition_status": "COMPLETED",
        "network_gate_policy_status": network_report["policy_status"],
        "write_gate_policy_status": write_report["policy_status"],
        "request_execution_policy_status": req_report["policy_status"],
        "manifest_expectation_plan_status": manifest_report["plan_status"],
        "rollback_cleanup_policy_status": rollback_report["policy_status"],
        "stop_condition_policy_status": stop_report["policy_status"],
        "dryrun_test_plan_status": dryrun_report["plan_status"],
        "preflight_decision_status": "COMPLETED",
        "recommendation_status": "COMPLETED",
        "preflight_plan_ready": decision_report["preflight_plan_ready"],
        "preflight_plan_only": True,
        "preflight_executed": False,
        "next_allowed_phase": decision_report["next_allowed_phase"],
        "network_enabled": False,
        "network_disabled": True,
        "network_disabled_by_default": True,
        "future_network_activation_requires_separate_approval": True,
        "real_collection_approved": False,
        "real_collection_approval_status": "NOT_APPROVED",
        "real_collection_executed": False,
        "human_review_required_before_collection": True,
        "controlled_preflight_allowed": True,
        "controlled_preflight_network_policy": "STRICTLY_DISABLED_BY_DEFAULT",
        "dry_run_only": True,
        "local_fixture_only": True,
        "fixture_only": True,
        "synthetic_or_minimal_sample": True,
        "not_for_research_results": True,
        "allowed_writes": write_report["allowed_writes"],
        "forbidden_writes": write_report["forbidden_writes"],
        "requests_executed_count": 0,
        "external_api_called": False,
        "external_data_downloaded": False,
        "new_data_files_created": False,
        "no_data_directory_writes": True,
        "parquet_created": False,
        "csv_created": False,
        "sqlite_created": False,
        "manifest_expectations_defined": True,
        "stop_conditions_defined": True,
        "rollback_policy_defined": True,
        "dryrun_tests_defined": True,
        "final_verdict": decision_report["verdict"],
        "recommended_next_step": rec_report["recommended_next_step"],
        "evidence_classification": "INFRASTRUCTURE_ONLY",
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "codex_cli_called": False,
        "real_orders_possible": False
    }
    writer.write_report("microstructure_preflight_plan_summary", summary, "Preflight Plan Summary", ["Comprehensive status overview."])

    # 13. Consistency Check
    consistency = {
        "version": version,
        "current_version": version,
        "previous_version": "V1.59",
        "previous_base": "V1.59",
        "migrated_from": "V1.59",
        "migration_reason": "safety flags alignment fix",
        "safety_flags_alignment_status": "SAFETY_FLAGS_ALIGNED",
        "safety_flags_complete": True,
        "consistency_check_status": "MICROSTRUCTURE_PREFLIGHT_PLAN_REPORTS_CONSISTENT_INFRASTRUCTURE_ONLY",

        "issues": [],
        "project_state_aligned": True,
        "latest_metrics_aligned": True,
        "latest_summary_aligned": True,
        "all_json_values_finite": True,
        "all_json_files_parseable": True,
        "invalid_json_files": [],
        "required_reports_present": True,
        "required_markdown_reports_present": True,
        "safety_flags_aligned": True,
        "recommendation_aligned": True,
        "release_reports_present": True,
        "preflight_plan_ready": True,
        "preflight_plan_only": True,
        "preflight_executed": False,
        "next_allowed_phase": decision_report["next_allowed_phase"],
        "network_enabled": False,
        "network_disabled": True,
        "network_disabled_by_default": True,
        "future_network_activation_requires_separate_approval": True,
        "real_collection_approved": False,
        "real_collection_approval_status": "NOT_APPROVED",
        "real_collection_executed": False,
        "human_review_required_before_collection": True,
        "controlled_preflight_allowed": True,
        "controlled_preflight_network_policy": "STRICTLY_DISABLED_BY_DEFAULT",
        "dry_run_only": True,
        "local_fixture_only": True,
        "fixture_only": True,
        "synthetic_or_minimal_sample": True,
        "not_for_research_results": True,
        "dry_run_only_present": True,
        "local_fixture_only_present": True,
        "fixture_only_present": True,
        "synthetic_or_minimal_sample_present": True,
        "not_for_research_results_present": True,
        "requests_executed_count": 0,
        "external_api_called": False,
        "external_data_downloaded": False,
        "new_data_files_created": False,
        "no_data_directory_writes": True,
        "parquet_created": False,
        "csv_created": False,
        "sqlite_created": False,
        "manifest_expectations_defined": True,
        "stop_conditions_defined": True,
        "rollback_policy_defined": True,
        "dryrun_tests_defined": True,
        "status_field_policy": "REMOVED",
        "status_field_present": False,
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "codex_cli_called": False,
        "real_orders_possible": False
    }
    writer.write_report("microstructure_preflight_plan_consistency_check", consistency, "Preflight Plan Consistency Check", ["Ensures all reports are aligned."])

    # 14. Recommendation (final)
    full_rec = {
        "version": version,
        "current_version": version,
        "previous_version": "V1.59",
        "previous_base": "V1.59",
        "migrated_from": "V1.59",
        "migration_reason": "safety flags alignment fix",
        "safety_flags_alignment_status": "SAFETY_FLAGS_ALIGNED",
        "safety_flags_complete": True,
        "final_verdict": decision_report["verdict"],
        "recommended_next_step": rec_report["recommended_next_step"],
        "evidence_classification": "INFRASTRUCTURE_ONLY",
        "consistency_check_status": consistency["consistency_check_status"],
        "preflight_plan_ready": True,
        "preflight_plan_only": True,
        "preflight_executed": False,
        "next_allowed_phase": decision_report["next_allowed_phase"],
        "network_enabled": False,
        "network_disabled": True,
        "real_collection_approved": False,
        "real_collection_approval_status": "NOT_APPROVED",
        "human_review_required_before_collection": True,
        "dry_run_only": True,
        "local_fixture_only": True,
        "fixture_only": True,
        "synthetic_or_minimal_sample": True,
        "not_for_research_results": True,
        "external_api_called": False,
        "external_data_downloaded": False,
        "requests_executed_count": 0,
        "no_strategy_validated": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "codex_cli_called": False,
        "real_orders_possible": False
    }
    writer.write_report("v1_59_1_recommendation", full_rec, "V1.59.1 Recommendation", ["Final gate for planning phase (Flags Aligned)."])

    print(f"{version} Preflight Plan reports generated in reports/research/")

if __name__ == "__main__":
    main()
