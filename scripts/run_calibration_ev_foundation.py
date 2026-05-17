from __future__ import annotations

import argparse
import pandas as pd
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from galapagos.research.calibration_ev.point_in_time_audit import audit_point_in_time_features
from galapagos.research.calibration_ev.prediction_frame_builder import build_prediction_frames
from galapagos.research.calibration_ev.calibration_metrics import calculate_calibration_metrics
from galapagos.research.calibration_ev.reliability_bins import analyze_reliability_bins
from galapagos.research.calibration_ev.temporal_calibration import analyze_temporal_calibration
from galapagos.research.calibration_ev.regime_calibration import analyze_regime_calibration
from galapagos.research.calibration_ev.payoff_asymmetry import analyze_payoff_asymmetry
from galapagos.research.calibration_ev.cost_model_foundation import audit_cost_model_foundation
from galapagos.research.calibration_ev.ev_diagnostic import run_ev_diagnostic
from galapagos.research.calibration_ev.recommendation_engine import generate_v1_30_recommendations
from galapagos.research.calibration_ev.report_writer import write_v1_30_reports

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--intrabar", required=True)
    parser.add_argument("--recent-summary", required=True)
    parser.add_argument("--version", default="v1.30")
    args = parser.parse_args()
    
    print(f"--- Running Calibration & EV Foundation {args.version} ---")
    
    # 1. Load data
    df_preds = pd.read_parquet(args.predictions)
    df_dataset = pd.read_parquet(args.dataset)
    
    # Merge dataset features to predictions (using timestamp)
    # This allows regime-based calibration even if not in original prediction parquet
    if "timestamp" in df_preds.columns and "timestamp" in df_dataset.columns:
        df_preds["timestamp"] = pd.to_datetime(df_preds["timestamp"], utc=True)
        df_dataset["timestamp"] = pd.to_datetime(df_dataset["timestamp"], utc=True)
        
        # Select useful causal columns from dataset
        causal_cols = ["timestamp", "macro_regime"]
        causal_cols = [c for c in causal_cols if c in df_dataset.columns]
        
        df_full = pd.merge(df_preds, df_dataset[causal_cols], on="timestamp", how="left")
    else:
        df_full = df_preds
        
    # 2. Audit & Build Frames
    pit_audit = audit_point_in_time_features(df_full)
    selection_frame, outcome_frame, integrity_report = build_prediction_frames(df_full)
    
    # 3. Global Calibration
    global_cal = calculate_calibration_metrics(
        outcome_frame["actual_target"].values,
        selection_frame["predicted_probability"].values
    )
    
    # 4. Reliability Bins
    rel_bins = analyze_reliability_bins(selection_frame, outcome_frame)
    
    # 5. Temporal Calibration
    temp_cal = analyze_temporal_calibration(selection_frame, outcome_frame)
    
    # 6. Regime Calibration
    reg_cal = analyze_regime_calibration(selection_frame, outcome_frame)
    
    # 7. Payoff Asymmetry
    payoff_asym = analyze_payoff_asymmetry(selection_frame, outcome_frame)
    
    # 8. Cost Model Audit
    cost_audit = audit_cost_model_foundation(outcome_frame)
    
    # 9. EV Diagnostic
    ev_diag = run_ev_diagnostic(selection_frame, outcome_frame)
    
    # 10. Summary & Recommendations
    summary_data = {
        "point_in_time_status": pit_audit["point_in_time_status"],
        "raw_dataset_contains_outcomes": pit_audit["raw_dataset_contains_outcomes"],
        "raw_dataset_outcomes_classified": pit_audit["raw_dataset_outcomes_classified"],
        "prediction_frame_integrity_status": integrity_report["integrity_status"],
        "selection_leakage_status": "CLEAN" if not integrity_report["forbidden_columns_in_selection"] else "LEAK_FOUND",
        "calibration_global_status": global_cal.get("status"),
        "calibration_temporal_status": temp_cal[-1]["status"] if temp_cal else "UNKNOWN",
        "calibration_regime_status": reg_cal[0]["status"] if reg_cal else "UNKNOWN",
        "payoff_asymmetry_status": payoff_asym[0]["payoff_asymmetry_status"] if payoff_asym else "UNKNOWN",
        "cost_model_status": cost_audit["cost_model_status"],
        "costs_isolated_from_gross": cost_audit["costs_isolated_from_gross"],
        "ev_proxy_status": ev_diag["ev_proxy_status"],
        "probability_threshold_status": "NOT_VALIDATED"
    }
    
    recs = generate_v1_30_recommendations(summary_data)
    summary_data.update(recs)
    
    # 11. Write Reports
    all_results = {
        "point_in_time_feature_audit": pit_audit,
        "prediction_frame_integrity": integrity_report,
        "calibration_global": global_cal,
        "reliability_bins": {"bins": rel_bins},
        "calibration_temporal": {"windows": temp_cal},
        "calibration_regime": {"regimes": reg_cal},
        "payoff_asymmetry": {"asymmetry": payoff_asym},
        "cost_model_foundation": cost_audit,
        "expected_value_proxy": ev_diag,
        "calibration_ev_summary": summary_data,
        "recommendation": recs
    }
    
    write_v1_30_reports(all_results, version=args.version)
    
    print(f"--- Finished {args.version}. Reports written to reports/research/ ---")

if __name__ == "__main__":
    main()
