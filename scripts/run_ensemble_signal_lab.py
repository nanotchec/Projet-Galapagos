from __future__ import annotations

import argparse
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

import numpy as np
import pandas as pd

from galapagos.research.ensemble.agreement import analyze_agreement_buckets
from galapagos.research.ensemble.candidate_builder import build_reviewer_candidates
from galapagos.research.ensemble.ensemble_scores import compute_agreement, compute_ensemble_scores
from galapagos.research.ensemble.evaluation import evaluate_ensemble_bucket
from galapagos.research.ensemble.signal_inputs import load_ensemble_inputs
from galapagos.research.report_models import write_research_report
from galapagos.utils.config_loader import load_yaml
from galapagos.utils.version import normalize_version


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Ensemble Signal Lab")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--version", default="v1.16.2")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    v_norm = normalize_version(args.version)
    config = load_yaml(args.config)
    
    if args.dry_run:
        print(f"DRY RUN: Running ensemble lab for {args.dataset} using {args.config}")
        return

    merged_df = load_ensemble_inputs(args.dataset, config["predictions_path"])
    if merged_df is None:
        print("Error: Could not load ensemble inputs. Run export_ml_predictions.py first.")
        return

    # Define windows for multi-window evaluation
    windows = {
        "2024": ("2024-01-01", "2024-12-31"),
        "2025": ("2025-01-01", "2025-12-31"),
        "2026": ("2026-01-01", "2026-04-30"),
    }
    
    # Model selection logic (Strictly separated by horizon)
    horizons = ["6bar", "12bar"]
    results_by_horizon = {}
    
    for horizon in horizons:
        target_col = f"target_up_after_cost_{horizon}"
        forward_return_col = f"forward_return_{horizon}"
        
        # Select models that target this specific horizon
        model_cols = [c for c in merged_df.columns if f"_{target_col}" in c]
        if not model_cols:
            print(f"No model columns found for horizon {horizon}.")
            continue
            
        print(f"Found {len(model_cols)} models for horizon {horizon}: {model_cols}")
        
        # Perform multi-window evaluation for this horizon
        window_results = {}
        for window_name, (start, end) in windows.items():
            mask = (merged_df["timestamp"] >= pd.to_datetime(start, utc=True)) & (merged_df["timestamp"] <= pd.to_datetime(end, utc=True))
            df_window = merged_df[mask].copy()
            
            if len(df_window) == 0:
                print(f"Warning: No data for window {window_name} / {horizon}")
                continue
                
            # Compute ensemble scores
            df_window["mean_probability"] = compute_ensemble_scores(df_window, model_cols, method="mean_probability")
            df_window["agreement_score"] = compute_agreement(df_window, model_cols)
            
            # Evaluate (default to mean_probability)
            res = evaluate_ensemble_bucket(df_window, "mean_probability", target_col, forward_return_col)
            window_results[window_name] = res

        # Random Same-Count Baseline for this horizon
        random_results = {}
        for window_name in window_results:
            start, end = windows[window_name]
            mask = (merged_df["timestamp"] >= pd.to_datetime(start, utc=True)) & (
                merged_df["timestamp"] <= pd.to_datetime(end, utc=True)
            )
            df_window = merged_df[mask]
            
            count = window_results[window_name]["count"]
            if count > 0:
                trials = []
                for _ in range(config.get("random_trials", 100)):
                    random_sample = df_window.sample(n=count)
                    trials.append(random_sample[forward_return_col].mean())
                
                random_mean = np.mean(trials)
                actual_mean = window_results[window_name]["mean_forward_return"]
                p_value = np.mean([t >= actual_mean for t in trials])
                
                random_results[window_name] = {
                    "random_mean": float(random_mean),
                    "actual_mean": float(actual_mean),
                    "p_value": float(p_value),
                    "beaten": bool(p_value < 0.05),
                    "count": int(count)
                }

        # Compare with best single model for this horizon
        comparison_results = {}
        for window_name in window_results:
            start, end = windows[window_name]
            mask = (merged_df["timestamp"] >= pd.to_datetime(start, utc=True)) & (
                merged_df["timestamp"] <= pd.to_datetime(end, utc=True)
            )
            df_window = merged_df[mask]
            
            best_single_ret = -1.0
            for m_col in model_cols:
                res = evaluate_ensemble_bucket(df_window, m_col, target_col, forward_return_col)
                ret = res.get("mean_cost_adjusted_forward_return", -1)
                if ret > best_single_ret:
                    best_single_ret = ret
            
            ensemble_ret = window_results[window_name].get("mean_cost_adjusted_forward_return", -1)
            comparison_results[window_name] = {
                "best_single_model_return": float(best_single_ret),
                "ensemble_return": float(ensemble_ret),
                "ensemble_beats_single": bool(ensemble_ret > best_single_ret)
            }

        # Analyze Agreement for this horizon
        merged_df[f"agreement_{horizon}"] = compute_agreement(merged_df, model_cols)
        agreement_report, agreement_verdict = analyze_agreement_buckets(
            merged_df, 
            f"agreement_{horizon}", 
            forward_return_col,
            cost_threshold=config.get("cost_threshold", 0.003)
        )
        
        # Convert agreement report to list of dicts for JSON serialization
        if not agreement_report.empty:
            agreement_data = agreement_report.to_dict(orient="records")
        else:
            agreement_data = []
        
        results_by_horizon[horizon] = {
            "window_results": window_results,
            "random_results": random_results,
            "comparison_results": comparison_results,
            "agreement_report": agreement_data,
            "agreement_verdict": agreement_verdict
        }

    # Consolidated Verdict Logic (CONSERVATIVE V1.16.3)
    ready_for_reviewer = False
    verdict = "ENSEMBLE_NOT_READY_FOR_REVIEWER"
    verdict_reason = "No horizon met all conservative criteria."
    best_horizon_found = None
    
    # Check latest window (2026) specifically
    latest_window = "2026"
    
    for horizon, data in results_by_horizon.items():
        w_res = data["window_results"]
        r_res = data["random_results"]
        c_res = data["comparison_results"]
        
        # All windows must be positive after costs
        all_pos = all(w_res[w].get("mean_cost_adjusted_forward_return", -1) > 0 for w in w_res)
        
        # All windows must beat random baseline
        all_random_beaten = all(r_res[w]["beaten"] for w in r_res)
        
        # Latest window status
        latest_pos = w_res.get(latest_window, {}).get("mean_cost_adjusted_forward_return", -1) > 0
        latest_random = r_res.get(latest_window, {}).get("beaten", False)
        c_res.get(latest_window, {}).get("ensemble_beats_single", True) # True if no single model beats it significantly
        
        # High agreement edge
        high_agreement_ok = data["agreement_verdict"] == "AGREEMENT_IMPROVES_SIGNAL"
        
        # Beats single model on at least 2 windows
        single_beaten_count = sum(1 for w in c_res if c_res[w]["ensemble_beats_single"])
        
        if not all_pos or not latest_pos:
            verdict = "ENSEMBLE_RECENT_WINDOW_FAILED"
            verdict_reason = f"Horizon {horizon} failed on latest window (positive={latest_pos})."
            continue
            
        if not all_random_beaten or not latest_random:
            verdict_reason = f"Horizon {horizon} did not beat random baseline on all windows."
            continue
            
        if not high_agreement_ok:
            verdict_reason = f"Horizon {horizon} has no economic edge even at high agreement."
            continue
            
        if single_beaten_count < 2:
            verdict_reason = f"Horizon {horizon} only beats single model on {single_beaten_count}/3 windows."
            continue
            
        # If we reach here, this horizon is READY
        ready_for_reviewer = True
        verdict = "ENSEMBLE_REVIEWER_CANDIDATES_READY"
        verdict_reason = f"Horizon {horizon} passed all conservative criteria."
        best_horizon_found = horizon
        break

    # Save Signal Lab Report
    lab_summary = {
        "version": v_norm.upper(),
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "ready_for_reviewer": ready_for_reviewer,
        "results_by_horizon": results_by_horizon,
        "latest_window": latest_window,
        "no_horizon_mixing": True,
        "best_horizon": best_horizon_found
    }
    
    write_research_report(
        name=f"ensemble_signal_lab_{v_norm}",
        payload=lab_summary,
        title=f"Ensemble Signal Lab {v_norm.upper()}",
        lines=[
            f"Verdict: {verdict}.",
            f"Reason: {verdict_reason}.",
            f"Ready for reviewer: {ready_for_reviewer}.",
            f"Best horizon: {best_horizon_found}.",
            f"Latest window ({latest_window}) success: {ready_for_reviewer}."
        ],
        output_dir="reports/research"
    )

    # Save Agreement Report
    agreement_payload = {h: results_by_horizon[h]["agreement_report"] for h in results_by_horizon}
    write_research_report(
        name=f"ensemble_agreement_{v_norm}",
        payload=agreement_payload,
        title=f"Ensemble Agreement Analysis {v_norm.upper()}",
        lines=[
            "Analysis of model agreement buckets vs performance.",
            f"Horizons covered: {list(results_by_horizon.keys())}."
        ],
        output_dir="reports/research"
    )

    # Candidate Building (Only if ready)
    if ready_for_reviewer:
        best_h = best_horizon_found or "12bar"
        target_col = f"target_up_after_cost_{best_h}"
        model_cols = [c for c in merged_df.columns if f"_{target_col}" in c]
        
        # Add scores to the FULL merged_df for candidate generation
        merged_df["mean_probability"] = compute_ensemble_scores(
            merged_df, model_cols, method="mean_probability"
        )
        merged_df["agreement_score"] = compute_agreement(merged_df, model_cols)
        
        candidate_path = Path(f"data/gold/reviewer_candidates/candidates_{v_norm}.jsonl")
        candidate_path.parent.mkdir(parents=True, exist_ok=True)
        
        build_reviewer_candidates(
            merged_df, 
            "mean_probability", 
            "agreement_score", 
            str(candidate_path),
            enabled=ready_for_reviewer
        )
        
        write_research_report(
            name=f"reviewer_candidates_{v_norm}",
            payload={"candidate_path": str(candidate_path), "ready_for_reviewer": True},
            title=f"Reviewer Candidates {v_norm.upper()}",
            lines=[
                f"Candidates generated at {candidate_path}.",
                "Status: READY"
            ],
            output_dir="reports/research"
        )
        print(f"Candidats générés : {candidate_path}")
    else:
        # Write diagnostic report instead of .jsonl
        diagnostic = {
            "candidate_generation_status": "disabled_not_ready",
            "verdict": verdict,
            "reason": verdict_reason,
            "ready_for_reviewer": False
        }
        write_research_report(
            name=f"reviewer_candidates_{v_norm}",
            payload=diagnostic,
            title=f"Reviewer Candidates Status {v_norm.upper()}",
            lines=[
                "Candidate generation: DISABLED.",
                f"Reason: {diagnostic['reason']}"
            ],
            output_dir="reports/research"
        )
        print(f"Candidate generation disabled because ensemble not ready: {verdict_reason}")

    print(f"Ensemble Signal Lab completed. Verdict: {verdict}")


if __name__ == "__main__":
    main()
