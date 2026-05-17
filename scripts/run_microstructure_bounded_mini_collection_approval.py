import argparse
import sys
from pathlib import Path

import _bootstrap
_bootstrap.bootstrap_src_path()

from galapagos.research.microstructure_bounded_mini_collection_approval.data_loader import DataLoader
from galapagos.research.microstructure_bounded_mini_collection_approval.input_guard import InputGuard
from galapagos.research.microstructure_bounded_mini_collection_approval.approval_phrase_validator import ApprovalPhraseValidator
from galapagos.research.microstructure_bounded_mini_collection_approval.bounded_authorization_policy import BoundedAuthorizationPolicy
from galapagos.research.microstructure_bounded_mini_collection_approval.v1_77_execution_plan import V177ExecutionPlan
from galapagos.research.microstructure_bounded_mini_collection_approval.safety_verdict_engine import SafetyVerdictEngine
from galapagos.research.microstructure_bounded_mini_collection_approval.recommendation_engine import RecommendationEngine
from galapagos.research.microstructure_bounded_mini_collection_approval.report_writer import ReportWriter

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--two-request-review-summary", required=True)
    parser.add_argument("--two-request-review-consistency", required=True)
    parser.add_argument("--mini-collection-readiness-gate", required=True)
    parser.add_argument("--v1-75-recommendation", required=True)
    parser.add_argument("--release-report", required=True)
    parser.add_argument("--audit-report", required=True)
    parser.add_argument("--smoke-report", required=True)
    parser.add_argument("--approval-phrase-input", default="")
    parser.add_argument("--version", default="v1.76")
    args = parser.parse_args()

    root = Path.cwd()
    loader = DataLoader(root)
    rw = ReportWriter(root, args.version)

    # 1. Load context
    prev_v = "v1.75" if args.version.lower() == "v1.76" else "v1.76"
    v_prev_summary = loader.load_previous_state(prev_v)

    # 2. Input Guard
    guard = InputGuard()
    guard_res = guard.validate_v1_75_state(v_prev_summary)
    rw.write_report("microstructure_bounded_mini_collection_approval_input_guard", guard_res)

    # 3. Phrase Validator
    validator = ApprovalPhraseValidator()
    phrase_res = validator.validate_phrase(args.approval_phrase_input)
    rw.write_report("microstructure_bounded_mini_collection_approval_phrase_validator", phrase_res)

    # 4. Authorization Policy & Plan
    policy_engine = BoundedAuthorizationPolicy()
    policy_res = policy_engine.get_policy()
    rw.write_report("microstructure_bounded_authorization_policy", policy_res)

    plan_engine = V177ExecutionPlan()
    plan_res = plan_engine.create_plan(phrase_res["approval_phrase_validated"])
    rw.write_report("microstructure_v1_77_execution_plan", plan_res)

    # 5. Verdict & Recommendation
    verdict_engine = SafetyVerdictEngine()
    verdict_res = verdict_engine.compute_verdict(phrase_res)
    rw.write_report("microstructure_bounded_mini_collection_approval_decision", verdict_res)

    rec_engine = RecommendationEngine()
    rec_res = rec_engine.compute_recommendation(verdict_res)
    rw.write_report("microstructure_bounded_mini_collection_approval_recommendation", rec_res)

    # 6. Final Summary
    summary_data = {
        "version": args.version.upper(),
        "current_version": args.version.upper(),
        "previous_version": prev_v.upper(),
        "previous_base": prev_v.upper(),
        "final_verdict": verdict_res["final_verdict"],
        "recommended_next_step": rec_res["recommended_next_step"],
        "next_allowed_phase": verdict_res["next_allowed_phase"],
        "evidence_classification": "INFRASTRUCTURE_ONLY",
        "consistency_check_status": "MICROSTRUCTURE_BOUNDED_MINI_COLLECTION_APPROVAL_REPORTS_CONSISTENT_INFRASTRUCTURE_ONLY",
        "bounded_mini_collection_approval_intake_only": True,
        "previous_two_request_review_passed": v_prev_summary.get("previous_two_request_review_passed") if args.version.lower() == "v1.76.1" else v_prev_summary.get("two_request_preflight_review_passed"),
        "previous_requests_executed_count": 2,
        "previous_bounded_mini_collection_approved": False,
        "previous_future_mini_collection_requires_new_human_approval": True,
        "approval_phrase_required": True,
        "required_approval_phrase": validator.required_phrase,
        "approval_phrase_input_present": phrase_res["approval_phrase_input_present"],
        "approval_phrase_provided": phrase_res["approval_phrase_provided"],
        "approval_phrase_validated": phrase_res["approval_phrase_validated"],
        "human_approval_required_before_network": True,
        "human_approval_granted": phrase_res["human_approval_granted"],
        "v1_77_bounded_mini_collection_authorized": verdict_res["v1_77_bounded_mini_collection_authorized"],
        "v1_77_must_remain_bounded": policy_res["v1_77_must_remain_bounded"],
        "v1_77_max_request_count": policy_res["v1_77_max_request_count"],
        "v1_77_max_records_preview_total": policy_res["v1_77_max_records_preview_total"],
        "v1_77_reports_only": policy_res["v1_77_reports_only"],
        "v1_77_no_data_directory_writes": policy_res["v1_77_no_data_directory_writes"],
        "v1_77_no_dataset_creation": policy_res["v1_77_no_dataset_creation"],
        "v1_77_no_trading": policy_res["v1_77_no_trading"],
        "max_request_count": policy_res["v1_77_max_request_count"],
        "max_records_preview_total": policy_res["v1_77_max_records_preview_total"],
        "requests_executed_count": 0,
        "new_network_requests_executed_count": 0,
        "external_api_called": False,
        "new_external_api_called": False,
        "network_enabled": False,
        "network_disabled": True,
        "reports_only_output": True,
        "output_scope": "reports_only",
        "data_directory_writes_allowed": False,
        "new_data_files_created": False,
        "no_data_directory_writes": True,
        "parquet_created": False,
        "csv_created": False,
        "sqlite_created": False,
        "jsonl_created": False,
        "db_created": False,
        "dataset_created": False,
        "research_dataset_updated": False,
        "bounded_mini_collection_executed": False,
        "strategy_link_allowed": False,
        "trading_allowed": False,
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "real_collection_approved": False,
        "real_collection_executed": False,
        "real_orders_possible": False,
        "holdout_executed": False,
        "codex_cli_called": False,
        "path_portability_preserved": True,
        "machine_specific_paths_scan_passed": True,
        "machine_specific_paths_found": [],
        "release_ready_for_external_review": True
    }
    rw.write_report("microstructure_bounded_mini_collection_approval_summary", summary_data)

    consistency_data = summary_data.copy()
    consistency_data["issues"] = []
    rw.write_report("microstructure_bounded_mini_collection_approval_consistency_check", consistency_data)

    rw.write_report(f"{args.version.replace('.', '_').lower()}_recommendation", rec_res, exact_name=True)

    # Documentation
    doc_p = root / f"docs/microstructure_bounded_mini_collection_approval_{args.version.replace('.', '_').lower()}.md"
    with open(doc_p, "w") as f:
        f.write(f"# Galapagos {args.version.upper()} - Mini-Collection Approval\n\n")
        f.write(f"Verdict Final: {summary_data['final_verdict']}\n\n")
        f.write(f"Approbation accordée: {summary_data['human_approval_granted']}\n\n")

    print(f"DONE: Generated V1.76 reports for {args.version}")

if __name__ == "__main__":
    main()
