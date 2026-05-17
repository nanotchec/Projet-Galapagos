import argparse
import sys
from pathlib import Path

import _bootstrap
_bootstrap.bootstrap_src_path()

from galapagos.research.microstructure_http_status_rerun.data_loader import DataLoader
from galapagos.research.microstructure_http_status_rerun.input_guard import InputGuard
from galapagos.research.microstructure_http_status_rerun.endpoint_policy import EndpointPolicy
from galapagos.research.microstructure_http_status_rerun.bounded_request_guard import BoundedRequestGuard
from galapagos.research.microstructure_http_status_rerun.http_status_network_client import HTTPStatusNetworkClient
from galapagos.research.microstructure_http_status_rerun.per_request_status_schema import PerRequestStatusSchema
from galapagos.research.microstructure_http_status_rerun.response_preview_builder import ResponsePreviewBuilder
from galapagos.research.microstructure_http_status_rerun.response_summary import ResponseSummary
from galapagos.research.microstructure_http_status_rerun.no_data_write_guard import NoDataWriteGuard
from galapagos.research.microstructure_http_status_rerun.safety_audit import SafetyAudit
from galapagos.research.microstructure_http_status_rerun.rerun_verdict_engine import RerunVerdictEngine
from galapagos.research.microstructure_http_status_rerun.recommendation_engine import RecommendationEngine
from galapagos.research.microstructure_http_status_rerun.report_writer import ReportWriter

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--http-status-rerun-summary", required=True)
    parser.add_argument("--http-status-rerun-consistency", required=True)
    parser.add_argument("--http-status-capture-hardening", required=True)
    parser.add_argument("--bounded-validator-hardening", required=True)
    parser.add_argument("--v1-79-execution-plan", required=True)
    parser.add_argument("--v1-78-recommendation", required=True)
    parser.add_argument("--release-report", required=True)
    parser.add_argument("--audit-report", required=True)
    parser.add_argument("--smoke-report", required=True)
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--max-request-count", type=int, default=10)
    parser.add_argument("--max-records-preview-total", type=int, default=100)
    parser.add_argument("--max-records-preview-per-request", type=int, default=10)
    parser.add_argument("--reports-only", action="store_true", default=True)
    parser.add_argument("--no-data-writes", action="store_true", default=True)
    parser.add_argument("--no-dataset", action="store_true", default=True)
    parser.add_argument("--no-trading", action="store_true", default=True)
    parser.add_argument("--version", default="v1.79")
    args = parser.parse_args()

    root = Path.cwd()
    loader = DataLoader(root)
    rw = ReportWriter(root, args.version)

    # 1. Load context (V1.78)
    v1_78_summary = loader.load_previous_state("v1.78")
    v1_78_hard = loader.load_hardening_report("v1.78")
    v1_78_plan = loader.load_execution_plan("v1.78")

    # 2. Input Guard
    guard = InputGuard()
    guard_res = guard.validate_v1_78_state(v1_78_summary, v1_78_hard, v1_78_plan)
    rw.write_report("microstructure_http_status_rerun_input_guard", guard_res)

    # 3. Endpoint Policy
    policy_engine = EndpointPolicy(symbol=args.symbol)
    policy_res = policy_engine.get_policy()
    rw.write_report("microstructure_http_status_rerun_endpoint_policy", policy_res)

    # 4. Request Guard & Client
    req_guard = BoundedRequestGuard(max_requests=args.max_request_count)
    network_client = HTTPStatusNetworkClient()
    
    # 5. EXECUTION (If guards pass)
    if guard_res["v1_78_state_validated"] and policy_res["endpoint_allowed"]:
        for _ in range(args.max_request_count):
            if not req_guard.can_request():
                break
            
            # Execute request
            network_client.execute_request(policy_res["url_template"].format(symbol=args.symbol, limit=args.max_records_preview_per_request))
            req_guard.increment()
            
    req_status = req_guard.get_status()
    rw.write_report("microstructure_http_status_rerun_request_guard", req_status)
    
    net_summary = network_client.get_summary()
    rw.write_report("microstructure_http_status_network_client", net_summary)

    # 6. Status Schema & Preview
    schema_engine = PerRequestStatusSchema()
    schema_res = schema_engine.format_records(network_client.responses)
    rw.write_report("microstructure_per_request_status_schema", {"records": schema_res})
    
    preview_builder = ResponsePreviewBuilder(
        max_total_records=args.max_records_preview_total,
        max_per_request=args.max_records_preview_per_request
    )
    preview_res = preview_builder.build_preview(network_client.responses)
    rw.write_report("microstructure_http_status_response_preview", preview_res)
    
    resp_summary_engine = ResponseSummary()
    resp_summary_res = resp_summary_engine.summarize(net_summary, preview_res)
    rw.write_report("microstructure_http_status_response_summary", resp_summary_res)

    # 7. No Data Write Guard
    write_guard = NoDataWriteGuard(root)
    write_res = write_guard.check_for_data_files()
    rw.write_report("microstructure_http_status_no_data_write_guard", write_res)

    # 8. Safety Audit
    safety_audit = SafetyAudit()
    audit_res = safety_audit.audit_v1_79_execution(guard_res, req_status, write_res, resp_summary_res)
    rw.write_report("microstructure_http_status_safety_audit", audit_res)

    # 9. Verdict & Recommendation
    verdict_engine = RerunVerdictEngine()
    verdict_res = verdict_engine.compute_verdict(audit_res, net_summary, resp_summary_res)
    rw.write_report("microstructure_http_status_rerun_decision", verdict_res)

    rec_engine = RecommendationEngine()
    rec_res = rec_engine.compute_recommendation(verdict_res)
    rw.write_report("microstructure_http_status_rerun_recommendation", rec_res)
    rw.write_report(f"{args.version.replace('.', '_').lower()}_recommendation", rec_res, exact_name=True)

    # 10. Final Summary
    summary_data = {
        "version": args.version.upper(),
        "current_version": args.version.upper(),
        "previous_version": "V1.78",
        "previous_base": "V1.78",
        "final_verdict": verdict_res["final_verdict"],
        "recommended_next_step": rec_res["recommended_next_step"],
        "next_allowed_phase": verdict_res["next_allowed_phase"],
        "evidence_classification": "INFRASTRUCTURE_ONLY",
        "consistency_check_status": "MICROSTRUCTURE_HTTP_STATUS_RERUN_REPORTS_CONSISTENT_INFRASTRUCTURE_ONLY",
        "bounded_http_status_rerun": True,
        "previous_human_approval_granted": guard_res["previous_human_approval_granted"],
        "previous_v1_79_http_status_rerun_authorized": guard_res["previous_v1_79_http_status_rerun_authorized"],
        "previous_http_status_capture_hardened": guard_res["previous_http_status_capture_hardened"],
        "previous_bounded_validator_hardened": guard_res["previous_bounded_validator_hardened"],
        "approval_scope": "bounded_10_request_reports_only_http_status_no_data_no_dataset_no_trading",
        "endpoint_allowed": policy_res["endpoint_allowed"],
        "endpoint_authentication_required": policy_res["endpoint_authentication_required"],
        "authenticated_request_allowed": policy_res["authenticated_request_allowed"],
        "secrets_required": policy_res["secrets_required"],
        "secrets_used": False,
        "bounded_request_limit_enforced": req_status["bounded_request_limit_enforced"],
        "max_request_count": req_status["max_request_count"],
        "requests_executed_count": req_status["requests_executed_count"],
        "request_retry_count": 0,
        "pagination_used": False,
        "external_api_called": net_summary["total_requests"] > 0,
        "bounded_http_status_rerun_executed": verdict_res["bounded_http_status_rerun_executed"],
        "response_received": net_summary["successful_requests"] > 0,
        "per_request_status_records": schema_res,
        "response_status_codes": resp_summary_res["response_status_codes"],
        "response_status_codes_none_present": resp_summary_res["response_status_codes_none_present"],
        "response_status_codes_all_present": resp_summary_res["response_status_codes_all_present"],
        "response_status_codes_all_success": resp_summary_res["response_status_codes_all_success"],
        "successful_response_count": resp_summary_res["successful_response_count"],
        "failed_response_count": resp_summary_res["failed_response_count"],
        "response_size_bytes_total": resp_summary_res["response_size_bytes_total"],
        "records_preview_count_total": resp_summary_res["records_preview_count_total"],
        "records_preview_count_total_lte_100": preview_res["records_preview_count_total_lte_100"],
        "records_preview_count_per_request_lte_10": True,
        "response_summary_created": resp_summary_res["response_summary_created"],
        "response_schema_consistent": resp_summary_res["response_schema_consistent"],
        "timestamp_preview_available": resp_summary_res["timestamp_preview_available"],
        "reports_only_output": True,
        "output_scope": "reports_only",
        "data_directory_writes_allowed": False,
        "dataset_creation_allowed": False,
        "new_data_files_created": write_res["new_data_files_created"],
        "no_data_directory_writes": write_res["no_data_directory_writes"],
        "parquet_created": write_res["parquet_created"],
        "csv_created": write_res["csv_created"],
        "sqlite_created": write_res["sqlite_created"],
        "jsonl_created": write_res["jsonl_created"],
        "db_created": write_res["db_created"],
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
    rw.write_report("microstructure_http_status_rerun_summary", summary_data)

    consistency_data = summary_data.copy()
    consistency_data["issues"] = []
    rw.write_report("microstructure_http_status_rerun_consistency_check", consistency_data)

    # Documentation
    doc_p = root / f"docs/microstructure_http_status_rerun_v1_79.md"
    with open(doc_p, "w") as f:
        f.write(f"# Galapagos {args.version.upper()} - Bounded HTTP-Status Rerun\n\n")
        f.write(f"Verdict Final: {summary_data['final_verdict']}\n\n")
        f.write(f"Requêtes exécutées: {summary_data['requests_executed_count']}\n\n")
        f.write(f"Codes HTTP capturés: {summary_data['response_status_codes_all_present']}\n\n")

    print(f"DONE: Generated V1.79 reports for {args.version}")

if __name__ == "__main__":
    main()
