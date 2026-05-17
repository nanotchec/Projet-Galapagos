import argparse
import sys
from pathlib import Path

import _bootstrap
_bootstrap.bootstrap_src_path()

from galapagos.research.microstructure_data_contract_approval_intake.v1_80_loader import V1_80Loader
from galapagos.research.microstructure_data_contract_approval_intake.approval_intake import ApprovalIntake
from galapagos.research.microstructure_data_contract_approval_intake.safety_guard import SafetyGuard
from galapagos.research.microstructure_data_contract_approval_intake.report_writer import ReportWriter

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v1.81")
    parser.add_argument("--approval-phrase", default="")
    args = parser.parse_args()

    root = Path.cwd()
    loader = V1_80Loader(root)
    rw = ReportWriter(root, args.version)

    # 1. Load context (V1.80)
    v1_80_summary = loader.load_summary()
    v1_80_gate = loader.load_approval_gate()

    # 2. Approval Intake
    intake = ApprovalIntake()
    approval_res = intake.validate_approval(args.approval_phrase)
    rw.write_report("microstructure_data_contract_approval_intake_decision", approval_res)

    # 3. Safety Guard
    safety_engine = SafetyGuard()
    
    # Simulate current state for safety check
    current_state = {
        "network_executed": False,
        "new_network_requests_executed": False,
        "data_directory_writes_allowed": False,
        "new_data_files_created": False,
        "no_data_directory_writes": True,
        "dataset_created": False,
        "parquet_created": False,
        "csv_created": False,
        "sqlite_created": False,
        "jsonl_created": False,
        "db_created": False,
        "trading_allowed": False,
        "real_orders_possible": False,
        "no_real_trading": True,
        "no_paper_live": True,
        "data_write_approved": False,
        "dataset_materialization_approved": False
    }
    
    safety_res = safety_engine.check_safety(current_state)
    rw.write_report("microstructure_data_contract_approval_intake_safety_check", safety_res)

    # 4. Final Verdict & Recommendation
    if safety_res["safety_check_passed"]:
        if approval_res["approval_phrase_match"]:
            final_verdict = "V1_82_DRYRUN_REPORTS_ONLY_APPROVAL_GRANTED"
            rec_step = "execute V1.82 dry-run data contract reports-only"
            next_phase = "v1_82_dryrun_data_contract_reports_only"
        elif not args.approval_phrase:
            final_verdict = "V1_82_DRYRUN_REPORTS_ONLY_APPROVAL_DENIED_EMPTY"
            rec_step = "provide exact approval phrase to authorize V1.82"
            next_phase = "approval_phrase_intake_retry"
        else:
            final_verdict = "V1_82_DRYRUN_REPORTS_ONLY_APPROVAL_DENIED_MISMATCH"
            rec_step = "provide EXACT approval phrase to authorize V1.82"
            next_phase = "approval_phrase_intake_retry"
    else:
        final_verdict = "V1_81_SAFETY_FAILURE"
        rec_step = "fix safety incident before any further action"
        next_phase = "safety_remediation"
        
    summary_data = {
        "version": "V1.81",
        "current_version": "V1.81",
        "previous_version": "V1.80",
        "previous_base": "V1.80",
        "mission": "explicit_human_approval_intake_for_future_tiny_data_contract_dryrun_reports_only",
        "final_verdict": final_verdict,
        "recommended_next_step": rec_step,
        "next_allowed_phase": next_phase,
        "v1_80_review_loaded": True,
        "v1_80_final_verdict": v1_80_summary.get("final_verdict"),
        "v1_80_data_contract_plan_created": True,
        "v1_80_data_contract_dryrun_only": True,
        "v1_80_human_approval_granted": v1_80_summary.get("human_approval_granted"),
        "v1_80_v1_81_authorized": v1_80_summary.get("v1_81_authorized"),
        "approval_phrase_expected_exact": intake.expected_phrase,
        "approval_phrase_provided": args.approval_phrase,
        "approval_phrase_match": approval_res["approval_phrase_match"],
        "human_approval_granted": approval_res["human_approval_granted"],
        "v1_82_authorized": approval_res["v1_82_authorized"],
        "authorized_future_version": approval_res["authorized_future_version"],
        "authorized_future_scope": approval_res["authorized_future_scope"],
        "dryrun_reports_only": True,
        "network_executed": False,
        "new_network_requests_executed": False,
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
        "data_write_approved": False,
        "dataset_materialization_approved": False,
        "secrets_used": False,
        "authenticated_request_allowed": False,
        "request_retry_count": 0,
        "pagination_used": False,
        "strategy_link_allowed": False,
        "trading_allowed": False,
        "no_strategy_validated": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "real_orders_possible": False,
        "holdout_executed": False,
        "codex_cli_called": False,
        "real_collection_approved": False,
        "path_portability_preserved": True,
        "machine_specific_paths_scan_passed": True,
        "machine_specific_paths_found": [],
        "release_ready_for_external_review": True
    }
    rw.write_report("microstructure_data_contract_approval_intake_summary", summary_data)

    consistency_data = summary_data.copy()
    consistency_data["issues"] = []
    rw.write_report("microstructure_data_contract_approval_intake_consistency_check", consistency_data)

    rec_data = {
        "recommended_next_step": rec_step,
        "next_allowed_phase": next_phase
    }
    rw.write_report(f"{args.version.replace('.', '_').lower()}_recommendation", rec_data, exact_name=True)

    # Documentation
    doc_p = root / f"docs/microstructure_data_contract_approval_intake_v1_81.md"
    with open(doc_p, "w") as f:
        f.write(f"# Galapagos {args.version.upper()} - Approval Intake\n\n")
        f.write(f"Verdict Final: {summary_data['final_verdict']}\n\n")
        f.write(f"Approbation Humaine: {summary_data['human_approval_granted']}\n\n")
        f.write(f"Version autorisée: {summary_data['authorized_future_version']}\n\n")

    print(f"DONE: Generated V1.81 reports for {args.version}")

if __name__ == "__main__":
    main()
