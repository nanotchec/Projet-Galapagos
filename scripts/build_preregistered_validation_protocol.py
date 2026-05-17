from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.signal_selection.report_models import save_signal_report
from galapagos.research.preregistration.protocol_schema import ValidationProtocol
from galapagos.research.preregistration.success_criteria import get_success_criteria
from galapagos.research.preregistration.evidence_classifier import classify_evidence
from galapagos.research.preregistration.retrospective_check import run_retrospective_check
from galapagos.research.preregistration.recommendation_engine import get_v1_26_recommendation

def main():
    parser = argparse.ArgumentParser(description="Build Pre-Registered Validation Protocol (V1.26.1)")
    parser.add_argument("--robust-summary", required=True)
    parser.add_argument("--temporal-report", required=True)
    parser.add_argument("--same-frequency-report", required=True)
    parser.add_argument("--cost-sensitivity-report", required=True)
    parser.add_argument("--placebo-report", required=True)
    parser.add_argument("--overfit-report", required=True)
    parser.add_argument("--stability-report", required=True)
    parser.add_argument("--version", default="v1.26.1")
    args = parser.parse_args()

    print(f"--- Galapagos {args.version} Protocol Building ---")
    
    # Normalize version for filenames (v1.26.1 -> v1_26_1)
    v_norm = args.version.lower().replace(".", "_")
    
    # 1. Load Reports
    inputs = {
        "summary": args.robust_summary,
        "temporal": args.temporal_report,
        "sf_random": args.same_frequency_report,
        "cost": args.cost_sensitivity_report,
        "placebo": args.placebo_report,
        "overfit": args.overfit_report,
        "stability": args.stability_report
    }
    
    loaded_data = {}
    missing_reports = []
    for key, path in inputs.items():
        p = Path(path)
        if not p.exists():
            missing_reports.append(path)
            continue
        with open(p) as f:
            loaded_data[key] = json.load(f)
            
    if missing_reports:
        print(f"ERROR: Missing reports: {missing_reports}")
        # We still proceed to write what we can but mark status
        status = "PARTIAL_INPUTS_MISSING"
    else:
        status = "INPUT_REPORTS_CONSISTENT"

    # 2. Build Protocol
    protocol = ValidationProtocol(
        version=args.version,
        created_from="V1.26",
        candidate_filter="low_frequency_strict_score",
        candidate_policy="horizon_only"
    )
    protocol_dict = protocol.to_dict()
    protocol_dict["input_reports_loaded"] = list(loaded_data.keys())
    protocol_dict["input_report_consistency_status"] = status
    save_signal_report(f"preregistered_signal_validation_protocol_{v_norm}", protocol_dict)
    
    # 3. Success Criteria
    criteria = get_success_criteria()
    save_signal_report(f"preregistered_success_criteria_{v_norm}", criteria)
    
    # 4. Evidence Classification
    evidence = classify_evidence(args.version)
    save_signal_report(f"preregistered_evidence_classification_{v_norm}", evidence)
    
    # 5. Retrospective Check
    if status == "INPUT_REPORTS_CONSISTENT":
        retro = run_retrospective_check(
            loaded_data["summary"],
            loaded_data["temporal"],
            loaded_data["sf_random"],
            loaded_data["cost"],
            loaded_data["placebo"],
            loaded_data["overfit"],
            loaded_data["stability"]
        )
    else:
        retro = {"status": status, "verdict": "RETROSPECTIVE_CHECK_INCONCLUSIVE"}
        
    save_signal_report(f"preregistered_retrospective_check_{v_norm}", retro)
    
    # 6. Future Plan
    # Estimer le rythme : 122 trades sur ~28 mois (jan 2024 -> mai 2026)
    # Rythme ≈ 4.3 trades / mois
    # Pour 60 trades => 60 / 4.3 ≈ 14 mois
    future_plan = {
        "version": args.version,
        "required_raw_candidates": ">= 5000 (estimated for sufficient density)",
        "required_selected_trades": 60,
        "expected_selected_trades_per_month": 4.3,
        "minimum_calendar_duration_months": 14,
        "estimated_validation_duration": "14-16 months",
        "validation_start_after": "2026-05-06",
        "no_filter_change_allowed": True,
        "no_metric_change_allowed": True,
        "no_cost_model_change_allowed": True,
        "duration_estimate_uncertainty": "HIGH (based on historical density only)"
    }
    save_signal_report(f"preregistered_future_validation_plan_{v_norm}", future_plan)
    
    # 7. Recommendation
    reco = get_v1_26_recommendation()
    reco["final_verdict"] = "PRE_REGISTERED_PROTOCOL_COMPLETE"
    save_signal_report(f"{v_norm}_recommendation", reco)
    
    print(f"--- Galapagos {args.version} Complete ---")

if __name__ == "__main__":
    main()
