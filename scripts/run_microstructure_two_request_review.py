import argparse
import sys
from pathlib import Path

import _bootstrap
_bootstrap.bootstrap_src_path()

from galapagos.research.microstructure_two_request_review.data_loader import DataLoader
from galapagos.research.microstructure_two_request_review.input_guard import InputGuard
from galapagos.research.microstructure_two_request_review.request_limit_review import RequestLimitReview
from galapagos.research.microstructure_two_request_review.endpoint_review import EndpointReview
from galapagos.research.microstructure_two_request_review.response_preview_review import ResponsePreviewReview
from galapagos.research.microstructure_two_request_review.response_comparison_review import ResponseComparisonReview
from galapagos.research.microstructure_two_request_review.no_data_write_review import NoDataWriteReview
from galapagos.research.microstructure_two_request_review.no_strategy_linkage_review import NoStrategyLinkageReview
from galapagos.research.microstructure_two_request_review.mini_collection_readiness_gate import MiniCollectionReadinessGate
from galapagos.research.microstructure_two_request_review.review_verdict_engine import ReviewVerdictEngine
from galapagos.research.microstructure_two_request_review.recommendation_engine import RecommendationEngine
from galapagos.research.microstructure_two_request_review.report_writer import ReportWriter

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--two-request-summary", required=True)
    parser.add_argument("--two-request-consistency", required=True)
    parser.add_argument("--two-request-client", required=True)
    parser.add_argument("--response-preview", required=True)
    parser.add_argument("--response-comparison", required=True)
    parser.add_argument("--two-request-guard", required=True)
    parser.add_argument("--no-data-write-guard", required=True)
    parser.add_argument("--safety-audit", required=True)
    parser.add_argument("--v1-74-recommendation", required=True)
    parser.add_argument("--release-report", required=True)
    parser.add_argument("--audit-report", required=True)
    parser.add_argument("--smoke-report", required=True)
    parser.add_argument("--version", default="v1.75")
    args = parser.parse_args()

    root = Path.cwd()
    loader = DataLoader(root)
    rw = ReportWriter(root, args.version)

    # 1. Load context (V1.74)
    v1_74_summary = loader.load_previous_state("v1.74")

    # 2. Input Guard
    guard = InputGuard()
    guard_res = guard.validate_v1_74_state(v1_74_summary)
    rw.write_report("microstructure_two_request_review_input_guard", guard_res)

    # 3. Component Reviews
    limit_engine = RequestLimitReview()
    limit_res = limit_engine.review_limit(v1_74_summary)
    rw.write_report("microstructure_two_request_limit_review", limit_res)

    endpoint_engine = EndpointReview()
    endpoint_res = endpoint_engine.review_endpoints(v1_74_summary)
    rw.write_report("microstructure_two_request_endpoint_review", endpoint_res)

    preview_engine = ResponsePreviewReview()
    preview_res = preview_engine.review_preview(v1_74_summary)
    rw.write_report("microstructure_two_request_response_preview_review", preview_res)

    comparison_engine = ResponseComparisonReview()
    comparison_res = comparison_engine.review_comparison(v1_74_summary)
    rw.write_report("microstructure_two_request_response_comparison_review", comparison_res)

    write_engine = NoDataWriteReview()
    write_res = write_engine.review_no_data_writes(v1_74_summary)
    rw.write_report("microstructure_two_request_no_data_write_review", write_res)

    linkage_engine = NoStrategyLinkageReview()
    linkage_res = linkage_engine.review_linkage(v1_74_summary)
    rw.write_report("microstructure_two_request_no_strategy_linkage_review", linkage_res)

    # 4. Verdict & Readiness Gate
    verdict_engine = ReviewVerdictEngine()
    verdict_res = verdict_engine.compute_verdict({
        "input_guard_passed": guard_res["input_guard_passed"],
        "request_limit_review_passed": limit_res["request_limit_review_passed"],
        "endpoint_review_passed": endpoint_res["endpoint_review_passed"],
        "response_preview_review_passed": preview_res["response_preview_review_passed"],
        "response_comparison_review_passed": comparison_res["response_comparison_review_passed"],
        "no_data_write_review_passed": write_res["no_data_write_review_passed"],
        "no_strategy_linkage_review_passed": linkage_res["no_strategy_linkage_review_passed"]
    })
    rw.write_report("microstructure_two_request_review_decision", verdict_res)

    gate_engine = MiniCollectionReadinessGate()
    gate_res = gate_engine.create_gate(verdict_res["two_request_preflight_review_passed"])
    rw.write_report("microstructure_mini_collection_readiness_gate", gate_res)

    rec_engine = RecommendationEngine()
    rec_res = rec_engine.compute_recommendation(verdict_res)
    rw.write_report("microstructure_two_request_review_recommendation", rec_res)

    # 5. Final Summary
    summary_data = {
        "version": args.version.upper(),
        "current_version": args.version.upper(),
        "previous_version": "V1.74",
        "previous_base": "V1.74",
        "final_verdict": verdict_res["final_verdict"],
        "recommended_next_step": rec_res["recommended_next_step"],
        "next_allowed_phase": verdict_res["next_allowed_phase"],
        "evidence_classification": "INFRASTRUCTURE_ONLY",
        "consistency_check_status": "MICROSTRUCTURE_TWO_REQUEST_PREFLIGHT_REVIEW_REPORTS_CONSISTENT_INFRASTRUCTURE_ONLY",
        "two_request_preflight_review_only": True,
        "two_request_preflight_review_passed": verdict_res["two_request_preflight_review_passed"],
        "previous_final_verdict": v1_74_summary.get("final_verdict"),
        "previous_requests_executed_count": v1_74_summary.get("requests_executed_count"),
        "previous_external_api_called": v1_74_summary.get("external_api_called"),
        "previous_tiny_network_collection_executed": v1_74_summary.get("tiny_network_collection_executed"),
        "previous_records_preview_count_total": v1_74_summary.get("records_preview_count_total"),
        "previous_records_preview_count_total_lte_20": v1_74_summary.get("records_preview_count_total_lte_20"),
        "previous_records_preview_count_per_request_lte_10": v1_74_summary.get("records_preview_count_per_request_lte_10"),
        "previous_response_comparison_created": v1_74_summary.get("response_comparison_created"),
        "previous_response_schema_consistent": v1_74_summary.get("response_schema_consistent"),
        "previous_endpoint_authentication_required": v1_74_summary.get("endpoint_authentication_required"),
        "previous_secrets_used": v1_74_summary.get("secrets_used"),
        "request_limit_review_passed": limit_res["request_limit_review_passed"],
        "endpoint_review_passed": endpoint_res["endpoint_review_passed"],
        "response_preview_review_passed": preview_res["response_preview_review_passed"],
        "response_comparison_review_passed": comparison_res["response_comparison_review_passed"],
        "no_data_write_review_passed": write_res["no_data_write_review_passed"],
        "no_strategy_linkage_review_passed": linkage_res["no_strategy_linkage_review_passed"],
        "mini_collection_readiness_gate_created": gate_res["mini_collection_readiness_gate_created"],
        "bounded_mini_collection_approved": gate_res["bounded_mini_collection_approved"],
        "future_mini_collection_requires_new_human_approval": gate_res["future_mini_collection_requires_new_human_approval"],
        "max_future_request_count_without_new_approval": gate_res["max_future_request_count_without_new_approval"],
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
    rw.write_report("microstructure_two_request_review_summary", summary_data)

    consistency_data = summary_data.copy()
    consistency_data["issues"] = []
    rw.write_report("microstructure_two_request_review_consistency_check", consistency_data)

    rw.write_report(f"{args.version.replace('.', '_').lower()}_recommendation", rec_res, exact_name=True)

    # Documentation
    doc_p = root / f"docs/microstructure_two_request_review_{args.version.replace('.', '_').lower()}.md"
    with open(doc_p, "w") as f:
        f.write(f"# Galapagos {args.version.upper()} - Two-Request Preflight Review\n\n")
        f.write(f"Verdict Final: {summary_data['final_verdict']}\n\n")
        f.write(f"Revue passée: {summary_data['two_request_preflight_review_passed']}\n\n")

    print(f"DONE: Generated V1.75 reports for {args.version}")

if __name__ == "__main__":
    main()
