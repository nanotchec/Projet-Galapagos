from __future__ import annotations

import argparse
import os
import sys

import pandas as pd

# Add src to path
sys.path.append(os.path.abspath("src"))

from galapagos.research.calibration_ev.prediction_frame_builder import build_prediction_frames
from galapagos.research.walk_forward_calibration.calibration_runner import run_walk_forward_calibration_suite
from galapagos.research.walk_forward_calibration.ev_after_calibration import diagnostic_ev_after_calibration
from galapagos.research.walk_forward_calibration.recommendation_engine import generate_v1_31_recommendation
from galapagos.research.walk_forward_calibration.report_writer import write_v1_31_reports
from galapagos.research.walk_forward_calibration.split_builder import build_walk_forward_splits


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--calibration-summary", required=True)
    parser.add_argument("--version", default="v1.31")
    args = parser.parse_args()
    
    print(f"--- Running Walk-Forward Calibration Research {args.version} ---")
    
    # 1. Load Data
    pred_df = pd.read_parquet(args.predictions)
    ds_df = pd.read_parquet(args.dataset)
    
    # Merge on timestamp. 
    # actual_target is already in pred_df for ml_predictions_v1_16_3.
    # We join with ds_df to get metadata/features if needed for building prediction frames.
    
    # Normalize timestamps to UTC to avoid merge errors
    pred_df["timestamp"] = pd.to_datetime(pred_df["timestamp"]).dt.tz_localize(None)
    ds_df["timestamp"] = pd.to_datetime(ds_df["timestamp"]).dt.tz_localize(None)
    
    common_cols = [c for c in ds_df.columns if c in pred_df.columns and c != "timestamp"]
    ds_cols = [c for c in ds_df.columns if c not in common_cols]
    
    df = pd.merge(pred_df, ds_df[ds_cols], on="timestamp", how="inner")
    
    # 2. Build Prediction Frames
    selection, outcome, integrity = build_prediction_frames(df)
    
    # We need actual_target for calibration, so we re-add it from outcome if needed
    # (Actually build_prediction_frames already separated them, but for runner we need both)
    # We'll work with a joined frame for splitting convenience
    full_df = selection.copy()
    full_df["actual_target"] = outcome["actual_target"]
    
    # 3. Build Splits
    splits = build_walk_forward_splits(full_df)
    
    # 4. Run Calibration Suite
    calibration_res = run_walk_forward_calibration_suite(full_df, splits)
    
    # 5. Extract Results
    all_results = calibration_res["results"]
    leakage_reports = calibration_res["leakage_reports"]
    
    # 6. Global Comparison
    # Calculate mean metrics per method
    comparison = []
    methods = set(r["method"] for r in all_results)
    for m in methods:
        m_results = [r for r in all_results if r["method"] == m]
        comparison.append({
            "method": m,
            "mean_brier": sum(r["brier_score"] for r in m_results) / len(m_results),
            "mean_ece": sum(r["ece"] for r in m_results) / len(m_results),
            "mean_mce": sum(r["mce"] for r in m_results) / len(m_results),
            "sample_count": sum(r["sample_count"] for r in m_results)
        })
        
    # 7. Summary & Recommendation
    # Find best method per metric
    best_method_ece = min(comparison, key=lambda x: x["mean_ece"])
    best_method_brier = min(comparison, key=lambda x: x["mean_brier"])
    raw_metrics = [c for c in comparison if c["method"] == "raw_probability"][0]
    
    # Calculate stability for 2026 H1
    # prend le split 2026_H1 ; comparer raw vs meilleure méthode calibrée selon ECE et selon Brier
    split_2026 = [r for r in all_results if r["split_id"] == "2026_H1"]
    raw_2026 = [r for r in split_2026 if r["method"] == "raw_probability"][0]
    
    # Best method by ECE in 2026_H1
    cal_2026_ece = min([r for r in split_2026 if r["method"] != "raw_probability"], key=lambda x: x["ece"])
    cal_2026_brier = min([r for r in split_2026 if r["method"] != "raw_probability"], key=lambda x: x["brier_score"])
    
    stable_2026 = (
        cal_2026_brier["brier_score"] < raw_2026["brier_score"]
        and cal_2026_ece["ece"] < raw_2026["ece"]
        and raw_2026["sample_count"] >= 1000
    )
    
    summary = {
        "raw_brier": raw_metrics["mean_brier"],
        "best_brier": best_method_brier["mean_brier"],
        "raw_ece": raw_metrics["mean_ece"],
        "best_ece": best_method_ece["mean_ece"],
        "best_method_by_ece": best_method_ece["method"],
        "best_method_by_brier": best_method_brier["method"],
        "best_method_selection_rule": "report multiple metric-specific winners; do not collapse to one universal best method",
        "calibration_improves_brier": best_method_brier["mean_brier"] < raw_metrics["mean_brier"],
        "calibration_improves_ece": best_method_ece["mean_ece"] < raw_metrics["mean_ece"],
        "calibration_stable_2026": stable_2026,
        "2026_raw_brier": raw_2026["brier_score"],
        "2026_calibrated_brier": cal_2026_brier["brier_score"],
        "2026_raw_ece": raw_2026["ece"],
        "2026_calibrated_ece": cal_2026_ece["ece"],
        "2026_brier_improved": cal_2026_brier["brier_score"] < raw_2026["brier_score"],
        "2026_ece_improved": cal_2026_ece["ece"] < raw_2026["ece"],
        "sample_count_2026": raw_2026["sample_count"]
    }
    
    recs = generate_v1_31_recommendation(summary)
    summary.update(recs)
    
    # 8. Write Reports
    reports = {
        "walk_forward_calibration_splits": [s.__dict__ for s in splits],
        "walk_forward_calibration_leakage_audit": leakage_reports,
        "walk_forward_calibration_comparison": comparison,
        "walk_forward_calibration_temporal": all_results,
        "walk_forward_reliability_bins": calibration_res["reliability_bins"],
        "walk_forward_calibration_summary": summary,
        "ev_after_calibration_diagnostic": diagnostic_ev_after_calibration(all_results),
        "recommendation": recs
    }
    
    write_v1_31_reports(reports, version=args.version)
    
    print(f"--- Finished {args.version}. Reports written to reports/research/ ---")


if __name__ == "__main__":
    main()
