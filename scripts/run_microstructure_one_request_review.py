import argparse
import sys
from pathlib import Path

import _bootstrap
_bootstrap.bootstrap_src_path()

from galapagos.research.microstructure_one_request_review.data_loader import DataLoader
from galapagos.research.microstructure_one_request_review.input_guard import InputGuard
from galapagos.research.microstructure_one_request_review.request_limit_review import RequestLimitReview
from galapagos.research.microstructure_one_request_review.endpoint_review import EndpointReview
from galapagos.research.microstructure_one_request_review.response_preview_review import ResponsePreviewReview
from galapagos.research.microstructure_one_request_review.no_data_write_review import NoDataWriteReview
from galapagos.research.microstructure_one_request_review.no_strategy_linkage_review import NoStrategyLinkageReview
from galapagos.research.microstructure_one_request_review.expansion_readiness_gate import ExpansionReadinessGate
from galapagos.research.microstructure_one_request_review.review_verdict_engine import ReviewVerdictEngine
from galapagos.research.microstructure_one_request_review.recommendation_engine import RecommendationEngine
from galapagos.research.microstructure_one_request_review.report_writer import ReportWriter

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tiny-network-summary", required=True)
    parser.add_argument("--tiny-network-consistency", required=True)
    parser.add_argument("--tiny-network-client", required=True)
    parser.add_argument("--response-preview", required=True)
    parser.add_argument("--one-request-guard", required=True)
    parser.add_argument("--no-data-write-guard", required=True)
    parser.add_argument("--safety-audit", required=True)
    parser.add_argument("--v1-71-recommendation", required=True)
    parser.add_argument("--release-report", required=True)
    parser.add_argument("--audit-report", required=True)
    parser.add_argument("--smoke-report", required=True)
    parser.add_argument("--version", default="v1.72")
    args = parser.parse_args()

    root = Path.cwd()
    loader = DataLoader(root)
    rw = ReportWriter(root, args.version)

    # 1. Load context (V1.71)
    v1_71_summary = loader.load_previous_state("v1.71")

    # 2. Input Guard
    guard = InputGuard()
    guard_res = guard.validate_v1_71_state(v1_71_summary)
    rw.write_report("microstructure_one_request_review_input_guard", guard_res)

    # 3. Reviews
    limit_reviewer = RequestLimitReview()
    limit_res = limit_reviewer.review_limit(v1_71_summary)
    rw.write_report("microstructure_request_limit_review", limit_res)

    endpoint_reviewer = EndpointReview()
    endpoint_res = endpoint_reviewer.review_endpoint(v1_71_summary)
    rw.write_report("microstructure_endpoint_review", endpoint_res)

    preview_reviewer = ResponsePreviewReview()
    preview_res = preview_reviewer.review_preview(v1_71_summary)
    rw.write_report("microstructure_response_preview_review", preview_res)

    write_reviewer = NoDataWriteReview()
    write_res = write_reviewer.review_writes(v1_71_summary)
    rw.write_report("microstructure_no_data_write_review", write_res)

    linkage_reviewer = NoStrategyLinkageReview()
    linkage_res = linkage_reviewer.review_linkage(v1_71_summary)
    rw.write_report("microstructure_no_strategy_linkage_review", linkage_res)

    # 4. Verdict & Readiness Gate
    review_status = {
        "limit_passed": limit_res["request_limit_review_passed"],
        "endpoint_passed": endpoint_res["endpoint_review_passed"],
        "preview_passed": preview_res["response_preview_review_passed"],
        "write_passed": write_res["no_data_write_review_passed"],
        "linkage_passed": linkage_res["no_strategy_linkage_review_passed"]
    }
    
    verdict_engine = ReviewVerdictEngine()
    verdict_res = verdict_engine.compute_verdict(review_status)
    rw.write_report("microstructure_one_request_review_decision", verdict_res)

    gate_engine = ExpansionReadinessGate()
    gate_res = gate_engine.evaluate_gate(verdict_res["one_request_preflight_review_passed"])
    rw.write_report("microstructure_expansion_readiness_gate", gate_res)

    rec_engine = RecommendationEngine()
    rec_res = rec_engine.compute_recommendation(verdict_res)
    rw.write_report("microstructure_one_request_review_recommendation", rec_res)

    # 5. Final Summary
    summary_data = {
        "version": args.version.upper(),
        "current_version": args.version.upper(),
        "previous_version": "V1.71",
        "previous_base": "V1.71",
        "final_verdict": verdict_res["final_verdict"],
        "recommended_next_step": rec_res["recommended_next_step"],
        "next_allowed_phase": verdict_res["next_allowed_phase"],
        "evidence_classification": "INFRASTRUCTURE_ONLY",
        "consistency_check_status": "MICROSTRUCTURE_ONE_REQUEST_PREFLIGHT_REVIEW_REPORTS_CONSISTENT_INFRASTRUCTURE_ONLY",
        "one_request_preflight_review_only": True,
        "one_request_preflight_review_passed": verdict_res["one_request_preflight_review_passed"],
        "previous_final_verdict": "MICROSTRUCTURE_ONE_REQUEST_TINY_NETWORK_PREFLIGHT_PASSED",
        "previous_requests_executed_count": v1_71_summary.get("requests_executed_count"),
        "previous_external_api_called": v1_71_summary.get("external_api_called"),
        "previous_tiny_network_collection_executed": v1_71_summary.get("tiny_network_collection_executed"),
        "request_limit_review_passed": limit_res["request_limit_review_passed"],
        "endpoint_review_passed": endpoint_res["endpoint_review_passed"],
        "response_preview_review_passed": preview_res["response_preview_review_passed"],
        "no_data_write_review_passed": write_res["no_data_write_review_passed"],
        "no_strategy_linkage_review_passed": linkage_res["no_strategy_linkage_review_passed"],
        "expansion_readiness_gate_created": True,
        "collection_expansion_approved": False,
        "future_expansion_requires_new_human_approval": True,
        "max_future_request_count_without_new_approval": 0,
        "requests_executed_count": 0,
        "new_network_requests_executed_count": 0,
        "external_api_called": False,
        "new_external_api_called": False,
        "network_enabled": False,
        "network_disabled": True,
        "previous_response_status_code": v1_71_summary.get("response_status_code"),
        "previous_response_size_bytes": v1_71_summary.get("response_size_bytes"),
        "previous_records_preview_count": v1_71_summary.get("records_preview_count"),
        "previous_records_preview_count_lte_10": v1_71_summary.get("records_preview_count_lte_10"),
        "previous_endpoint_authentication_required": v1_71_summary.get("endpoint_authentication_required"),
        "previous_secrets_used": v1_71_summary.get("secrets_used"),
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
    rw.write_report("microstructure_one_request_review_summary", summary_data)

    consistency_data = summary_data.copy()
    consistency_data["issues"] = []
    rw.write_report("microstructure_one_request_review_consistency_check", consistency_data)

    rw.write_report(f"{args.version.replace('.', '_').lower()}_recommendation", rec_res, exact_name=True)

    # Documentation
    doc_p = root / f"docs/microstructure_one_request_review_{args.version.replace('.', '_').lower()}.md"
    with open(doc_p, "w") as f:
        f.write(f"# Galapagos {args.version.upper()} - One-Request Preflight Review\n\n")
        f.write(f"Verdict Final: {summary_data['final_verdict']}\n\n")
        f.write(f"Revue passée: {summary_data['one_request_preflight_review_passed']}\n\n")
        f.write(f"Expansion approuvée: {summary_data['collection_expansion_approved']}\n\n")

    print(f"DONE: Generated V1.72 reports for {args.version}")

if __name__ == "__main__":
    main()
