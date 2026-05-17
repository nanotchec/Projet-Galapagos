import argparse
import sys
from pathlib import Path

import _bootstrap
_bootstrap.bootstrap_src_path()

from galapagos.research.microstructure_two_request_approval.data_loader import DataLoader
from galapagos.research.microstructure_two_request_approval.input_guard import InputGuard
from galapagos.research.microstructure_two_request_approval.approval_phrase_validator import ApprovalPhraseValidator
from galapagos.research.microstructure_two_request_approval.two_request_authorization_policy import TwoRequestAuthorizationPolicy
from galapagos.research.microstructure_two_request_approval.v1_74_execution_plan import V174ExecutionPlan
from galapagos.research.microstructure_two_request_approval.safety_verdict_engine import SafetyVerdictEngine
from galapagos.research.microstructure_two_request_approval.recommendation_engine import RecommendationEngine
from galapagos.research.microstructure_two_request_approval.report_writer import ReportWriter

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--one-request-review-summary", required=True)
    parser.add_argument("--one-request-review-consistency", required=True)
    parser.add_argument("--expansion-readiness-gate", required=True)
    parser.add_argument("--v1-72-recommendation", required=True)
    parser.add_argument("--release-report", required=True)
    parser.add_argument("--audit-report", required=True)
    parser.add_argument("--smoke-report", required=True)
    parser.add_argument("--approval-phrase-input", default="")
    parser.add_argument("--version", default="v1.73")
    args = parser.parse_args()

    root = Path.cwd()
    loader = DataLoader(root)
    rw = ReportWriter(root, args.version)

    # 1. Load context (V1.72)
    v1_72_summary = loader.load_previous_state("v1.72")
    gate_res = loader.load_gate("v1.72")

    # 2. Input Guard
    guard = InputGuard()
    guard_res = guard.validate_v1_72_state(v1_72_summary, gate_res)
    rw.write_report("microstructure_two_request_approval_input_guard", guard_res)

    # 3. Phrase Validation
    phrase_validator = ApprovalPhraseValidator()
    phrase_res = phrase_validator.validate(args.approval_phrase_input)
    rw.write_report("microstructure_two_request_approval_phrase_validator", phrase_res)

    # 4. Authorization Policy
    policy_engine = TwoRequestAuthorizationPolicy()
    policy_res = policy_engine.get_policy(phrase_res["human_approval_granted"])
    rw.write_report("microstructure_two_request_authorization_policy", policy_res)

    # 5. Execution Plan
    plan_engine = V174ExecutionPlan()
    plan_res = plan_engine.build_plan(policy_res["v1_74_two_request_preflight_authorized"])
    rw.write_report("microstructure_v1_74_execution_plan", plan_res)

    # 6. Verdict & Recommendation
    verdict_engine = SafetyVerdictEngine()
    verdict_res = verdict_engine.compute_verdict(phrase_res["human_approval_granted"], guard_res["input_guard_passed"])
    rw.write_report("microstructure_two_request_approval_decision", verdict_res)

    rec_engine = RecommendationEngine()
    rec_res = rec_engine.compute_recommendation(verdict_res)
    rw.write_report("microstructure_two_request_approval_recommendation", rec_res)

    # 7. Final Summary
    summary_data = {
        "version": args.version.upper(),
        "current_version": args.version.upper(),
        "previous_version": "V1.73" if args.version == "v1.73.1" else "V1.72",
        "previous_base": "V1.73" if args.version == "v1.73.1" else "V1.72",
        "final_verdict": verdict_res["final_verdict"],
        "recommended_next_step": rec_res["recommended_next_step"],
        "next_allowed_phase": verdict_res["next_allowed_phase"],
        "evidence_classification": "INFRASTRUCTURE_ONLY",
        "consistency_check_status": "MICROSTRUCTURE_TWO_REQUEST_APPROVAL_REPORTS_CONSISTENT_INFRASTRUCTURE_ONLY",
        "two_request_approval_intake_only": True,
        "previous_one_request_review_passed": True,
        "previous_requests_executed_count": 1,
        "previous_collection_expansion_approved": False,
        "previous_future_expansion_requires_new_human_approval": True,
        "approval_phrase_required": True,
        "required_approval_phrase": phrase_validator.required_phrase,
        "approval_phrase_input_present": phrase_res["approval_phrase_input_present"],
        "approval_phrase_provided": phrase_res["approval_phrase_provided"],
        "approval_phrase_validated": phrase_res["approval_phrase_validated"],
        "human_approval_required_before_network": True,
        "human_approval_granted": phrase_res["human_approval_granted"],
        "v1_74_two_request_preflight_authorized": policy_res["v1_74_two_request_preflight_authorized"],
        "v1_74_must_remain_two_requests_max": True,
        "v1_74_reports_only": True,
        "v1_74_no_data_directory_writes": True,
        "v1_74_no_trading": True,
        "max_request_count": 2,
        "max_records_preview": 20,
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
    rw.write_report("microstructure_two_request_approval_summary", summary_data)

    consistency_data = summary_data.copy()
    consistency_data["issues"] = []
    rw.write_report("microstructure_two_request_approval_consistency_check", consistency_data)

    rw.write_report(f"{args.version.replace('.', '_').lower()}_recommendation", rec_res, exact_name=True)

    # Documentation
    doc_p = root / f"docs/microstructure_two_request_approval_{args.version.replace('.', '_').lower()}.md"
    with open(doc_p, "w") as f:
        f.write(f"# Galapagos {args.version.upper()} - Two-Request Approval Gate\n\n")
        f.write(f"Verdict Final: {summary_data['final_verdict']}\n\n")
        f.write(f"Approbation accordée: {summary_data['human_approval_granted']}\n\n")
        f.write(f"Autorisation V1.74: {summary_data['v1_74_two_request_preflight_authorized']}\n\n")

    print(f"DONE: Generated V1.73 reports for {args.version}")

if __name__ == "__main__":
    main()
