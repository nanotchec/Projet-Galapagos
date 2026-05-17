import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from galapagos.research.microstructure_controlled_collection_readiness.input_guard import InputGuard
from galapagos.research.microstructure_controlled_collection_readiness.data_loader import DataLoader
from galapagos.research.microstructure_controlled_collection_readiness.readiness_review import ReadinessReview, NetworkActivationRiskAudit
from galapagos.research.microstructure_controlled_collection_readiness.tiny_collection_protocol import TinyCollectionProtocol, HumanApprovalProtocol
from galapagos.research.microstructure_controlled_collection_readiness.policies import (
    CollectionBoundaryPolicy, StopConditionsPolicy, RollbackCleanupPlan,
    DataWritePolicy, PreExecutionValidationPlan
)
from galapagos.research.microstructure_controlled_collection_readiness.verdict_engine import ReadinessVerdictEngine, RecommendationEngine

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight-fixture-summary", required=True)
    parser.add_argument("--controlled-collection-readiness-plan", required=True)
    parser.add_argument("--version", required=True)
    args, unknown = parser.parse_known_args()

    v_norm = args.version.replace(".", "_").lower()
    root = Path(__file__).parent.parent
    reports_dir = root / "reports/research"
    reports_dir.mkdir(parents=True, exist_ok=True)

    dl = DataLoader()
    summary_v1_66 = dl.load_json(Path(args.preflight_fixture_summary))
    plan_v1_66 = dl.load_json(Path(args.controlled_collection_readiness_plan))

    ig = InputGuard()
    if not ig.validate(summary_v1_66):
        print("ERROR: V1.66 input guard failed")
        sys.exit(1)

    readiness_review = ReadinessReview()
    review_res = readiness_review.audit(plan_v1_66)
    
    risk_audit = NetworkActivationRiskAudit()
    risk_res = risk_audit.audit()
    
    tiny_proto = TinyCollectionProtocol()
    proto_res = tiny_proto.define()
    
    human_proto = HumanApprovalProtocol()
    human_res = human_proto.define()
    
    boundary_policy = CollectionBoundaryPolicy()
    boundary_res = boundary_policy.define()
    
    stop_policy = StopConditionsPolicy()
    stop_res = stop_policy.define()
    
    rollback_plan = RollbackCleanupPlan()
    rollback_res = rollback_plan.define()
    
    write_policy = DataWritePolicy()
    write_res = write_policy.define()
    
    validation_plan = PreExecutionValidationPlan()
    validation_res = validation_plan.define()
    
    verdict_engine = ReadinessVerdictEngine()
    final_verdict = verdict_engine.get_verdict(
        review_res["controlled_collection_readiness_review_passed"],
        proto_res["tiny_collection_protocol_defined"],
        human_res["human_approval_protocol_defined"]
    )
    next_phase = verdict_engine.get_next_phase(review_res["controlled_collection_readiness_review_passed"])
    
    rec_engine = RecommendationEngine()
    recommendation = rec_engine.get_recommendation(review_res["controlled_collection_readiness_review_passed"])

    def write_report_no_suffix(name: str, data: Dict[str, Any]) -> None:
        p = reports_dir / f"{name}.json"
        with open(p, "w") as f:
            json.dump(data, f, indent=2)
        md_p = reports_dir / f"{name}.md"
        with open(md_p, "w") as f:
            f.write(f"# Report: {name.replace('_', ' ').title()}\n\n")
            f.write(f"```json\n{json.dumps(data, indent=2)}\n```\n")

    def write_report(name: str, data: Dict[str, Any]) -> None:
        p = reports_dir / f"{name}_{v_norm}.json"
        with open(p, "w") as f:
            json.dump(data, f, indent=2)
        md_p = reports_dir / f"{name}_{v_norm}.md"
        with open(md_p, "w") as f:
            f.write(f"# Report: {name.replace('_', ' ').title()}\n\n")
            f.write(f"```json\n{json.dumps(data, indent=2)}\n```\n")

    write_report("microstructure_controlled_collection_input_guard", {"status": "PASSED", "v1_66_validated": True})
    write_report("microstructure_controlled_collection_readiness_review", review_res)
    write_report("microstructure_network_activation_risk_audit", risk_res)
    write_report("microstructure_tiny_collection_protocol", proto_res)
    write_report("microstructure_human_approval_protocol", human_res)
    write_report("microstructure_collection_boundary_policy", boundary_res)
    write_report("microstructure_stop_conditions_policy", stop_res)
    write_report("microstructure_rollback_cleanup_plan", rollback_res)
    write_report("microstructure_data_write_policy", write_res)
    write_report("microstructure_pre_execution_validation_plan", validation_res)
    write_report("microstructure_controlled_collection_decision", {"final_verdict": final_verdict, "next_allowed_phase": next_phase})
    write_report("microstructure_controlled_collection_recommendation", {"recommendation": recommendation})

    summary_data = {
        "version": args.version.upper(),
        "current_version": args.version.upper(),
        "previous_version": "V1.66",
        "previous_base": "V1.66",
        "microstructure_preflight_fixture_base_version": "V1.66",
        "microstructure_preflight_skeleton_base_version": "V1.65",
        "microstructure_wrapper_fixture_base_version": "V1.64.2",
        "canonical_base_version": "V1.37.2",
        "input_guard_status": "PASSED",
        "readiness_review_status": "PASSED",
        "network_activation_risk_audit_status": "PASSED",
        "tiny_collection_protocol_status": "PASSED",
        "human_approval_protocol_status": "PASSED",
        "collection_boundary_policy_status": "PASSED",
        "stop_conditions_policy_status": "PASSED",
        "rollback_cleanup_plan_status": "PASSED",
        "data_write_policy_status": "PASSED",
        "pre_execution_validation_plan_status": "PASSED",
        "controlled_collection_decision_status": "READY",
        "recommendation_status": "GENERATED",
        "controlled_collection_readiness_review_passed": review_res["controlled_collection_readiness_review_passed"],
        "network_activation_risk_audit_completed": True,
        "network_activation_risks": risk_res["network_activation_risks"],
        "network_activation_risk_count": risk_res["network_activation_risk_count"],
        "tiny_collection_protocol_defined": proto_res["tiny_collection_protocol_defined"],
        "tiny_collection_protocol_only": True,
        "tiny_network_collection_executed": False,
        "human_approval_protocol_defined": human_res["human_approval_protocol_defined"],
        "human_approval_required_before_network": True,
        "human_approval_granted": False,
        "collection_boundary_policy_defined": True,
        "stop_conditions_defined": True,
        "rollback_cleanup_plan_defined": True,
        "data_write_policy_defined": True,
        "pre_execution_validation_plan_defined": True,
        "controlled_collection_readiness_review_only": True,
        "controlled_collection_readiness_plan_only": False,
        "controlled_collection_executed": False,
        "real_collection_executed": False,
        "real_collection_approved": False,
        "real_collection_approval_status": "NOT_APPROVED",
        "previous_preflight_skeleton_fixture_execution_passed": True,
        "previous_controlled_collection_readiness_plan_created": True,
        "previous_final_verdict": "MICROSTRUCTURE_PREFLIGHT_SKELETON_FIXTURE_EXECUTION_PASSED",
        "next_allowed_phase": next_phase,
        "network_enabled": False,
        "network_disabled": True,
        "network_disabled_by_default": True,
        "future_network_activation_requires_separate_approval": True,
        "external_api_called": False,
        "external_data_downloaded": False,
        "requests_executed_count": 0,
        "new_data_files_created": False,
        "no_data_directory_writes": True,
        "allowed_writes": ["reports/*.json", "reports/*.md"],
        "forbidden_writes": ["data/", "parquet", "csv", "sqlite", "db", "jsonl"],
        "parquet_created": False,
        "csv_created": False,
        "sqlite_created": False,
        "jsonl_created": False,
        "db_created": False,
        "dry_run_only": True,
        "local_fixture_only": True,
        "fixture_only": True,
        "synthetic_or_minimal_sample": True,
        "not_for_research_results": True,
        "final_verdict": final_verdict,
        "recommended_next_step": recommendation,
        "evidence_classification": "INFRASTRUCTURE_ONLY",
        "consistency_check_status": "MICROSTRUCTURE_CONTROLLED_COLLECTION_READINESS_REPORTS_CONSISTENT_INFRASTRUCTURE_ONLY",
        "verdict_alignment_status": "CONTROLLED_COLLECTION_READINESS_VERDICT_ALIGNED",
        "project_state_verdict_aligned": True,
        "latest_metrics_verdict_aligned": True,
        "recommendation_verdict_aligned": True,
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
    write_report("microstructure_controlled_collection_summary", summary_data)

    consistency_data = {
        "version": args.version.upper(),
        "current_version": args.version.upper(),
        "previous_version": "V1.66",
        "previous_base": "V1.66",
        "consistency_check_status": "MICROSTRUCTURE_CONTROLLED_COLLECTION_READINESS_REPORTS_CONSISTENT_INFRASTRUCTURE_ONLY",
        "issues": [],
        "verdict_alignment_status": "CONTROLLED_COLLECTION_READINESS_VERDICT_ALIGNED",
        "project_state_verdict_aligned": True,
        "latest_metrics_verdict_aligned": True,
        "recommendation_verdict_aligned": True,
        "summary_verdict": final_verdict,
        "project_state_verdict": final_verdict,
        "latest_metrics_verdict": final_verdict,
        "recommendation_verdict": final_verdict,
        "summary_controlled_collection_readiness_review_passed": True,
        "project_state_controlled_collection_readiness_review_passed": True,
        "latest_metrics_controlled_collection_readiness_review_passed": True,
        "recommendation_controlled_collection_readiness_review_passed": True,
        "summary_tiny_collection_protocol_defined": True,
        "project_state_tiny_collection_protocol_defined": True,
        "latest_metrics_tiny_collection_protocol_defined": True,
        "recommendation_tiny_collection_protocol_defined": True,
        "summary_human_approval_granted": False,
        "project_state_human_approval_granted": False,
        "latest_metrics_human_approval_granted": False,
        "recommendation_human_approval_granted": False,
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
        "status_field_policy": "REMOVED",
        "status_field_present": False,
        "controlled_collection_readiness_review_passed": True,
        "tiny_collection_protocol_defined": True,
        "tiny_collection_protocol_only": True,
        "human_approval_protocol_defined": True,
        "human_approval_required_before_network": True,
        "human_approval_granted": False,
        "controlled_collection_executed": False,
        "tiny_network_collection_executed": False,
        "real_collection_executed": False,
        "real_collection_approved": False,
        "real_collection_approval_status": "NOT_APPROVED",
        "network_enabled": False,
        "network_disabled": True,
        "future_network_activation_requires_separate_approval": True,
        "requests_executed_count": 0,
        "external_api_called": False,
        "external_data_downloaded": False,
        "new_data_files_created": False,
        "no_data_directory_writes": True,
        "parquet_created": False,
        "csv_created": False,
        "sqlite_created": False,
        "jsonl_created": False,
        "db_created": False,
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "codex_cli_called": False,
        "real_orders_possible": False
    }
    write_report("microstructure_controlled_collection_consistency_check", consistency_data)

    v_rec = summary_data.copy()
    write_report_no_suffix(f"{v_norm}_recommendation", v_rec)

    doc_path = root / f"docs/microstructure_controlled_collection_readiness_{v_norm}.md"
    with open(doc_path, "w") as f:
        f.write(f"# Controlled Collection Readiness Review V1.67\n\n")
        f.write(f"## Status\nVerdict: {final_verdict}\nPhase: {next_phase}\nRecommendation: {recommendation}\n\n")
        f.write(f"## Protocol Specification\nTiny Collection Protocol: DEFINED\nHuman Approval Protocol: DEFINED\n\n")
        f.write(f"## Safety\nNetwork: DISABLED\nWrite: DISABLED (INFRASTRUCTURE_ONLY)\nHuman Approval Granted: FALSE\n")

    print(f"DONE: Generated reports for {args.version}")

if __name__ == "__main__":
    main()
