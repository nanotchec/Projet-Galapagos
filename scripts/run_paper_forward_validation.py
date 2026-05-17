from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
import pandas as pd

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.signal_selection.report_models import save_signal_report
from galapagos.research.paper_forward.protocol_loader import load_and_verify_protocol
from galapagos.research.paper_forward.data_availability import check_data_availability
from galapagos.research.paper_forward.frozen_filter import validate_filter_definition
from galapagos.research.paper_forward.validation_engine import run_paper_forward_validation
from galapagos.research.paper_forward.mock_audit import run_mock_audit
from audit_protocol_immutability import calculate_protocol_hash, run_protocol_immutability_audit

def main():
    parser = argparse.ArgumentParser(description="Run Paper-Forward Validation (V1.27.3)")
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--success-criteria", required=True)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--intrabar", required=True)
    parser.add_argument("--version", default="v1.27.3")
    parser.add_argument("--reference-end-timestamp", default="2026-05-06T20:35:00Z")
    args = parser.parse_args()

    print(f"--- Galapagos {args.version} Paper-Forward Harness (Consistency Fix) ---")
    v_norm = args.version.lower().replace(".", "_")
    
    # 0. Initial Hash for Immutability Audit
    initial_hash = calculate_protocol_hash(args.protocol)
    
    # 1. Protocol Check
    proto_res = load_and_verify_protocol(args.protocol)
    save_signal_report(f"paper_forward_protocol_check_{v_norm}", proto_res)
    
    protocol = proto_res.get("protocol", {})
    
    # 2. Frozen Filter Audit
    filter_audit = validate_filter_definition(protocol)
    save_signal_report(f"paper_forward_frozen_filter_audit_{v_norm}", filter_audit)
    
    # 3. Data Availability
    data_res = check_data_availability(
        args.predictions, args.dataset, args.intrabar, args.reference_end_timestamp
    )
    save_signal_report(f"paper_forward_data_availability_{v_norm}", data_res)
    
    # 4. Mock Audit
    mock_res = run_mock_audit("src/galapagos/research/paper_forward")
    save_signal_report(f"paper_forward_mock_audit_{v_norm}", mock_res)
    
    # 5. Success Criteria
    try:
        with open(args.success_criteria) as f:
            criteria = json.load(f)
    except:
        criteria = {}
        
    # 6. Validation Engine
    preds_df = pd.DataFrame()
    if Path(args.predictions).exists():
        try:
            preds_df = pd.read_parquet(args.predictions)
        except:
            pass
            
    val_res = run_paper_forward_validation(
        protocol, criteria, preds_df, pd.DataFrame(), pd.DataFrame(), args.reference_end_timestamp
    )
    # Ensure logical priority in reason
    if not filter_audit.get("exact_filter_reconstructable", False):
        val_res["reason"] = "FROZEN_FILTER_DEFINITION_INSUFFICIENT"
        val_res["criteria_status"] = "NOT_EVALUATED_FILTER_NOT_RECONSTRUCTABLE"
        
    save_signal_report(f"paper_forward_validation_status_{v_norm}", val_res)
    
    # 7. Protocol Immutability Audit
    immutability_res = run_protocol_immutability_audit(args.protocol, initial_hash)
    save_signal_report(f"paper_forward_protocol_immutability_{v_norm}", immutability_res)
    
    # 8. Harness Readiness (Unified logic)
    reconstructable = filter_audit.get("exact_filter_reconstructable", False)
    read_ok = all(s == "READ_OK" for s in data_res.get("source_read_status", {}).values())
    no_mocks = not mock_res.get("mock_components_present", True)
    no_mutation = not immutability_res.get("protocol_mutated_during_run", True)
    
    if not no_mutation:
        status = "PAPER_FORWARD_HARNESS_FAILED_PROTOCOL_MUTATION"
    elif not no_mocks:
        status = "PAPER_FORWARD_HARNESS_FAILED_MOCKS_DETECTED"
    elif not reconstructable:
        status = "PAPER_FORWARD_HARNESS_PARTIAL_FILTER_DEFINITION_INSUFFICIENT"
    elif not read_ok:
        status = "PAPER_FORWARD_HARNESS_PARTIAL"
    elif not data_res.get("has_new_out_of_sample_data"):
        status = "PAPER_FORWARD_HARNESS_READY_NO_NEW_DATA"
    elif val_res.get("criteria_status") == "INCONCLUSIVE_NEEDS_MORE_DATA":
        status = "PAPER_FORWARD_HARNESS_READY_INCONCLUSIVE"
    else:
        status = "PAPER_FORWARD_HARNESS_READY"
        
    readiness = {
        "status": status,
        "protocol_check_status": proto_res.get("status"),
        "protocol_immutability_passed": no_mutation,
        "data_availability_status": data_res.get("status"),
        "frozen_filter_audit_status": filter_audit.get("status"),
        "exact_filter_reconstructable": reconstructable,
        "mock_audit_status": mock_res["status"],
        "mock_components_present": not no_mocks,
        "validation_status": val_res.get("criteria_status"),
        "harness_readiness_status": status,
        "reports_generated": True
    }
    save_signal_report(f"paper_forward_harness_readiness_{v_norm}", readiness)
    
    # 9. Recommendation
    reco = {
        "final_verdict": status,
        "protocol_reference": "v1.26.6",
        "filter_reconstructable": reconstructable,
        "has_new_oos_data": data_res.get("has_new_out_of_sample_data", False),
        "validation_status": val_res.get("criteria_status", "NOT_EVALUATED"),
        "selected_count": val_res.get("selected_count", 0),
        "minimum_required_selected_trades": 60,
        "future_validation_required": True,
        "ready_for_reviewer": False,
        "holdout_executed": False,
        "no_real_trading": True,
        "recommended_next_step": "collect future OOS data and rerun periodically."
    }
    
    if status.startswith("PAPER_FORWARD_HARNESS_FAILED"):
        reco["final_verdict"] = status
        reco["recommended_next_step"] = "Fix non-compliance issues (mutation or mocks)."
    elif status == "PAPER_FORWARD_HARNESS_READY_INCONCLUSIVE":
        reco["final_verdict"] = "PAPER_FORWARD_VALIDATION_INCONCLUSIVE_NEEDS_MORE_DATA"
        reco["recommended_next_step"] = "continue accumulating OOS trades until 60 selected trades."
        
    save_signal_report(f"{v_norm}_recommendation", reco)
    
    print(f"--- Galapagos {args.version} Complete ---")

if __name__ == "__main__":
    main()
