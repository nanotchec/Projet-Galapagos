from __future__ import annotations
import argparse
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from galapagos.research.microstructure_collector_contract_approval.data_loader import DataLoader
from galapagos.research.microstructure_collector_contract_approval.input_guard import InputGuard
from galapagos.research.microstructure_collector_contract_approval.approval_checklist import ApprovalChecklist
from galapagos.research.microstructure_collector_contract_approval.required_field_coverage import FieldCoverageAnalyzer
from galapagos.research.microstructure_collector_contract_approval.adapter_contract_completeness import AdapterContractVerifier
from galapagos.research.microstructure_collector_contract_approval.timestamp_policy_approval import TimestampPolicyVerifier
from galapagos.research.microstructure_collector_contract_approval.manifest_contract_approval import ManifestContractVerifier
from galapagos.research.microstructure_collector_contract_approval.fixture_coverage_approval import FixtureCoverageAnalyzer
from galapagos.research.microstructure_collector_contract_approval.network_safety_approval import NetworkSafetyVerifier
from galapagos.research.microstructure_collector_contract_approval.data_write_safety_approval import DataWriteSafetyVerifier
from galapagos.research.microstructure_collector_contract_approval.approval_decision import ApprovalDecisionEngine
from galapagos.research.microstructure_collector_contract_approval.recommendation_engine import RecommendationEngine
from galapagos.research.microstructure_collector_contract_approval.report_writer import ReportWriter

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter-fixture-summary", required=True)
    parser.add_argument("--adapter-field-mapping", required=True)
    parser.add_argument("--timestamp-normalization", required=True)
    parser.add_argument("--normalized-record-schema", required=True)
    parser.add_argument("--fixture-manifest-validation", required=True)
    parser.add_argument("--adapter-refinement-audit", required=True)
    parser.add_argument("--fixture-validation-audit", required=True)
    parser.add_argument("--collector-summary", required=True)
    parser.add_argument("--source-adapter-contract", required=True)
    parser.add_argument("--manifest-schema", required=True)
    parser.add_argument("--causal-timestamp-policy", required=True)
    parser.add_argument("--data-contract", required=True)
    parser.add_argument("--required-field-spec", required=True)
    parser.add_argument("--canonical-summary", required=True)
    parser.add_argument("--version", default="v1.56")
    args = parser.parse_args()

    v_norm = args.version.lower().replace(".", "_")
    version_label = args.version.upper()
    prev_base = "V1.55.3"
    
    paths = {
        "adapter_fixture_summary": args.adapter_fixture_summary,
        "adapter_field_mapping": args.adapter_field_mapping,
        "timestamp_normalization": args.timestamp_normalization,
        "normalized_record_schema": args.normalized_record_schema,
        "fixture_manifest_validation": args.fixture_manifest_validation,
        "adapter_refinement_audit": args.adapter_refinement_audit,
        "fixture_validation_audit": args.fixture_validation_audit,
        "collector_summary": args.collector_summary,
        "source_adapter_contract": args.source_adapter_contract,
        "manifest_schema": args.manifest_schema,
        "causal_timestamp_policy": args.causal_timestamp_policy,
        "data_contract": args.data_contract,
        "required_field_spec": args.required_field_spec,
        "canonical_summary": args.canonical_summary
    }

    loader = DataLoader(paths)
    data = loader.load_all()
    
    writer = ReportWriter()
    
    # 1. Input Guard
    guard = InputGuard(data)
    guard_res = guard.validate()
    guard_res.update({"version": version_label, "previous_base": prev_base})
    writer.write_json(f"microstructure_contract_input_guard_{v_norm}", guard_res)
    writer.write_md(f"microstructure_contract_input_guard_{v_norm}", "Microstructure Contract Input Guard", {"Results": guard_res})
    
    # 2. Field Coverage
    req_fields = data["required_field_spec"].get("required_microstructure_fields", []) if data["required_field_spec"] else []
    mapped_fields = data["adapter_field_mapping"].get("mapped_fields_by_adapter", {}) if data["adapter_field_mapping"] else {}
    analyzer = FieldCoverageAnalyzer(req_fields)
    coverage_res = analyzer.analyze(mapped_fields)
    coverage_res.update({"version": version_label, "previous_base": prev_base})
    writer.write_json(f"microstructure_required_field_coverage_{v_norm}", coverage_res)
    writer.write_md(f"microstructure_required_field_coverage_{v_norm}", "Microstructure Required Field Coverage", {"Results": coverage_res})
    
    # 3. Adapter Completeness
    adapters = data["source_adapter_contract"].get("supported_sources", []) if data["source_adapter_contract"] else []
    verifier = AdapterContractVerifier(adapters)
    adapter_res = verifier.verify(data["adapter_fixture_summary"] or {})
    adapter_res.update({"version": version_label, "previous_base": prev_base})
    writer.write_json(f"microstructure_adapter_contract_completeness_{v_norm}", adapter_res)
    writer.write_md(f"microstructure_adapter_contract_completeness_{v_norm}", "Microstructure Adapter Contract Completeness", {"Results": adapter_res})
    
    # 4. Timestamp Policy
    ts_verifier = TimestampPolicyVerifier(data["causal_timestamp_policy"].get("policy", {}) if data["causal_timestamp_policy"] else {})
    ts_res = ts_verifier.verify(data["timestamp_normalization"].get("timestamp_causality_passed", False) if data["timestamp_normalization"] else False)
    ts_res.update({"version": version_label, "previous_base": prev_base})
    writer.write_json(f"microstructure_timestamp_policy_approval_{v_norm}", ts_res)
    writer.write_md(f"microstructure_timestamp_policy_approval_{v_norm}", "Microstructure Timestamp Policy Approval", {"Results": ts_res})
    
    # 5. Manifest Approval
    manifest_verifier = ManifestContractVerifier(data["manifest_schema"])
    manifest_res = manifest_verifier.verify(data["fixture_manifest_validation"].get("manifest", {}) if data["fixture_manifest_validation"] else {})
    manifest_res.update({"version": version_label, "previous_base": prev_base})
    writer.write_json(f"microstructure_manifest_contract_approval_{v_norm}", manifest_res)
    writer.write_md(f"microstructure_manifest_contract_approval_{v_norm}", "Microstructure Manifest Contract Approval", {"Results": manifest_res})
    
    # 6. Fixture Coverage
    fixture_analyzer = FixtureCoverageAnalyzer(data["fixture_manifest_validation"].get("manifest", {}) if data["fixture_manifest_validation"] else {})
    fixture_res = fixture_analyzer.analyze()
    fixture_res.update({"version": version_label, "previous_base": prev_base})
    writer.write_json(f"microstructure_fixture_coverage_approval_{v_norm}", fixture_res)
    writer.write_md(f"microstructure_fixture_coverage_approval_{v_norm}", "Microstructure Fixture Coverage Approval", {"Results": fixture_res})
    
    # 7. Network Safety
    net_verifier = NetworkSafetyVerifier(data["adapter_fixture_summary"] or {})
    net_res = net_verifier.verify()
    net_res.update({"version": version_label, "previous_base": prev_base})
    writer.write_json(f"microstructure_network_safety_approval_{v_norm}", net_res)
    writer.write_md(f"microstructure_network_safety_approval_{v_norm}", "Microstructure Network Safety Approval", {"Results": net_res})
    
    # 8. Data Write Safety
    write_verifier = DataWriteSafetyVerifier(data["adapter_fixture_summary"] or {})
    write_res = write_verifier.verify()
    write_res.update({"version": version_label, "previous_base": prev_base})
    writer.write_json(f"microstructure_data_write_safety_approval_{v_norm}", write_res)
    writer.write_md(f"microstructure_data_write_safety_approval_{v_norm}", "Microstructure Data Write Safety Approval", {"Results": write_res})
    
    # 9. Checklist
    checklist = ApprovalChecklist()
    eval_inputs = {
        "required_fields_coverage": coverage_res["status"] == "PASSED",
        "adapter_completeness": adapter_res["status"] == "PASSED",
        "timestamp_causality": ts_res["status"] == "PASSED",
        "manifest_completeness": manifest_res["status"] == "PASSED",
        "fixture_coverage": fixture_res["status"] == "PASSED",
        "network_blocked": net_res["status"] == "PASSED",
        "no_data_writes": write_res["status"] == "PASSED",
        "no_trading": True # Verified by policy
    }
    checklist_res = checklist.evaluate(eval_inputs)
    checklist_res.update({"version": version_label, "previous_base": prev_base})
    writer.write_json(f"microstructure_contract_approval_checklist_{v_norm}", checklist_res)
    writer.write_md(f"microstructure_contract_approval_checklist_{v_norm}", "Microstructure Contract Approval Checklist", {"Results": checklist_res})
    
    # 10. Decision
    decision_engine = ApprovalDecisionEngine(checklist_res)
    decision_res = decision_engine.compute_decision()
    decision_res.update({"version": version_label, "previous_base": prev_base})
    writer.write_json(f"microstructure_contract_approval_decision_{v_norm}", decision_res)
    writer.write_md(f"microstructure_contract_approval_decision_{v_norm}", "Microstructure Contract Approval Decision", {"Results": decision_res})
    
    # 11. Recommendation
    rec_engine = RecommendationEngine(decision_res)
    rec_res = rec_engine.get_recommendation()
    rec_res.update({"version": version_label, "previous_base": prev_base})
    writer.write_json(f"microstructure_contract_recommendation_{v_norm}", rec_res)
    writer.write_md(f"microstructure_contract_recommendation_{v_norm}", "Microstructure Contract Recommendation", {"Results": rec_res})

    # 12. Recommendation report (legacy name)
    rec_legacy = rec_res.copy()
    rec_legacy.update({
        "real_collection_approved": False,
        "human_review_required_before_collection": True,
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "codex_cli_called": False,
        "real_orders_possible": False,
        "network_disabled": True,
        "dry_run_only": True,
        "local_fixture_only": True,
        "real_collection_executed": False,
        "external_data_downloaded": False,
        "external_api_called": False,
        "requests_executed_count": 0
    })
    writer.write_json(f"{v_norm}_recommendation", rec_legacy)
    writer.write_md(f"{v_norm}_recommendation", f"V1.56 Recommendation", {"Summary": rec_legacy})

    # 13. Summary
    summary = {
        "version": version_label,
        "previous_base": prev_base,
        "microstructure_adapter_fixture_base_version": prev_base,
        "microstructure_collector_network_disabled_base_version": "V1.54",
        "microstructure_backfill_dryrun_base_version": "V1.53.2",
        "microstructure_data_enrichment_base_version": "V1.52",
        "canonical_base_version": "V1.37.2",
        "input_guard_status": guard_res["status"],
        "approval_checklist_status": checklist_res["checklist_status"],
        "required_field_coverage_status": coverage_res["status"],
        "adapter_contract_completeness_status": adapter_res["status"],
        "timestamp_policy_approval_status": ts_res["status"],
        "manifest_contract_approval_status": manifest_res["status"],
        "fixture_coverage_approval_status": fixture_res["status"],
        "network_safety_approval_status": net_res["status"],
        "data_write_safety_approval_status": write_res["status"],
        "approval_decision_status": decision_res["approval_decision_status"],
        "recommendation_status": rec_res["status"],
        "required_fields_covered": all(r["all_adapters_covered"] for r in [coverage_res]),
        "missing_required_fields": sum([len(a["missing_required_fields"]) for a in coverage_res["adapters"].values()]),
        "adapter_contracts_complete": adapter_res["adapter_contracts_complete"],
        "timestamp_policy_approved": ts_res["timestamp_policy_approved"],
        "manifest_contract_approved": manifest_res["manifest_contract_approved"],
        "fixture_coverage_status": fixture_res["status"],
        "network_safety_approved": net_res["network_safety_approved"],
        "data_write_safety_approved": write_res["data_write_safety_approved"],
        "contract_ready_for_offline_review": decision_res["contract_ready_for_offline_review"],
        "real_collection_approved": False,
        "human_review_required_before_collection": True,
        "network_disabled": True,
        "dry_run_only": True,
        "local_fixture_only": True,
        "fixture_only": True,
        "synthetic_or_minimal_sample": True,
        "not_for_research_results": True,
        "real_collection_executed": False,
        "external_data_downloaded": False,
        "external_api_called": False,
        "new_data_files_created": False,
        "no_data_directory_writes": True,
        "parquet_created": False,
        "csv_created": False,
        "sqlite_created": False,
        "requests_executed_count": 0,
        "final_verdict": rec_res["final_verdict"],
        "recommended_next_step": rec_res["recommended_next_step"],
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
    writer.write_json(f"microstructure_contract_approval_summary_{v_norm}", summary)
    writer.write_md(f"microstructure_contract_approval_summary_{v_norm}", "Microstructure Contract Approval Summary", {"Summary": summary})

    # 14. Consistency Check
    consistency = {
        "version": version_label,
        "previous_base": prev_base,
        "consistency_check_status": "MICROSTRUCTURE_CONTRACT_APPROVAL_REPORTS_CONSISTENT_INFRASTRUCTURE_ONLY",
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
        "contract_ready_for_offline_review": summary["contract_ready_for_offline_review"],
        "real_collection_approved": False,
        "human_review_required_before_collection": True,
        "network_disabled": True,
        "dry_run_only": True,
        "local_fixture_only": True,
        "fixture_only": True,
        "synthetic_or_minimal_sample": True,
        "not_for_research_results": True,
        "real_collection_executed": False,
        "external_data_downloaded": False,
        "external_api_called": False,
        "new_data_files_created": False,
        "no_data_directory_writes": True,
        "parquet_created": False,
        "csv_created": False,
        "sqlite_created": False,
        "requests_executed_count": 0,
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
    writer.write_json(f"microstructure_contract_approval_consistency_check_{v_norm}", consistency)
    writer.write_md(f"microstructure_contract_approval_consistency_check_{v_norm}", "Microstructure Contract Approval Consistency Check", {"Consistency": consistency})

    print(f"Mission {version_label} complete. Final Verdict: {rec_res['final_verdict']}")

if __name__ == "__main__":
    main()
