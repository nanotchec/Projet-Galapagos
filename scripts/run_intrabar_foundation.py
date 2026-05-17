"""Orchestrator for intrabar foundation research."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.intrabar.alignment import align_intrabar_to_parent
from galapagos.research.intrabar.availability import check_availability
from galapagos.research.intrabar.cost_model import evaluate_cost_stress
from galapagos.research.intrabar.downloader import download_intrabar_sample
from galapagos.research.intrabar.execution_simulator import simulate_intrabar_exit
from galapagos.research.intrabar.mae_mfe import calculate_mae_mfe
from galapagos.research.intrabar.report import write_intrabar_report


def find_real_signals() -> tuple[pd.DataFrame | None, dict[str, Any]]:
    """Try to find real signals in the codebase and audit them."""
    audit = {
        "raw_signal_rows": 0,
        "unique_signal_timestamps": 0,
        "duplicate_signal_rows": 0,
        "duplicates_per_timestamp_max": 0,
        "models_count": 0,
        "feature_sets_count": 0,
        "targets_count": 0,
        "selected_signal_policy": "max_predicted_probability"
    }
    paths = [
        "data/gold/ml_predictions/BTC/4h/ml_predictions_v1_16_3.parquet",
        "data/gold/ml_predictions/BTC/4h/ml_predictions_v1_16_2.parquet",
        "data/gold/ml_predictions/BTC/4h/ml_predictions_v1_16_1.parquet",
        "data/gold/ml_predictions/BTC/4h/ml_predictions_v1_16.parquet",
    ]
    for p in paths:
        if Path(p).exists():
            print(f"Found real signals at {p}")
            df = pd.read_parquet(p)
            # Ensure timestamp is datetime
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            if df["timestamp"].dt.tz is None:
                df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
            
            # Audit raw signals (predicted_label == 1)
            if "predicted_label" in df.columns:
                signals_raw = df[df["predicted_label"] == 1].copy()
                audit["raw_signal_rows"] = len(signals_raw)
                
                if not signals_raw.empty:
                    audit["models_count"] = signals_raw["model_name"].nunique() if "model_name" in signals_raw.columns else 0
                    audit["feature_sets_count"] = signals_raw["feature_set"].nunique() if "feature_set" in signals_raw.columns else 0
                    audit["targets_count"] = signals_raw["target"].nunique() if "target" in signals_raw.columns else 0
                    
                    # Group by timestamp to check for duplicates
                    ts_counts = signals_raw.groupby("timestamp").size()
                    audit["unique_signal_timestamps"] = len(ts_counts)
                    audit["duplicate_signal_rows"] = audit["raw_signal_rows"] - audit["unique_signal_timestamps"]
                    audit["duplicates_per_timestamp_max"] = int(ts_counts.max())
                    
                    # Deduplicate: keep max predicted_probability
                    if "predicted_probability" in signals_raw.columns:
                        signals_dedup = signals_raw.sort_values("predicted_probability", ascending=False).drop_duplicates("timestamp")
                    else:
                        signals_dedup = signals_raw.drop_duplicates("timestamp")
                    
                    signals_dedup["candidate_side"] = "LONG"
                    return signals_dedup, audit
                    
    return None, audit


def run_orchestrator(symbol: str, timeframe: str, days: int, version: str, dry_run: bool) -> None:
    v_suffix = version.replace(".", "_")
    
    # 1. Availability
    print("Checking availability...")
    avail = check_availability(["binance", "bybit"], symbol, [timeframe], dry_run=dry_run)
    # the check script does the reporting for availability usually, but we'll do it here as well for completeness if needed,
    # Actually the instruction said to generate the reports.
    write_intrabar_report(
        f"intrabar_availability_{v_suffix}",
        {"status": "checked", "results": avail},
        f"Intrabar Availability {version}",
        ["Verdict: **INTRABAR_5M_PUBLIC_AVAILABLE**" if any(a["status"] == "available" for a in avail) else "Verdict: **INTRABAR_DRY_RUN_MOCKED**"]
    )
    
    # 2. Download
    print("Fetching sample...")
    dl_res = download_intrabar_sample("binance", symbol, timeframe, days, dry_run=dry_run)
    
    dl_verdict = "INTRABAR_SAMPLE_FETCH_SUCCESS"
    if dl_res["status"] == "failed":
        dl_verdict = "INTRABAR_FETCH_FAILED"
    elif dry_run:
        dl_verdict = "INTRABAR_SAMPLE_DRY_RUN"
        
    write_intrabar_report(
        f"intrabar_download_{v_suffix}",
        dl_res,
        f"Intrabar Download {version}",
        [f"Verdict: **{dl_verdict}**"]
    )
    
    # 3. Signals Discovery
    print("Searching for real signals...")
    real_signals_df, signal_audit = find_real_signals()
    
    simulation_input_type = "artificial_placeholder"
    if real_signals_df is not None:
        simulation_input_type = "real_signal_timestamps_with_artificial_exit_assumptions"
    
    # Setup DFs
    if dl_res["status"] != "success" or dry_run:
        parent_df = pd.DataFrame({"timestamp": [pd.Timestamp("2026-01-01", tz="UTC")]})
        intrabar_df = pd.DataFrame({"timestamp": [], "open": [], "high": [], "low": [], "close": []})
        min_ts = pd.Timestamp("2026-01-01", tz="UTC")
        max_ts = pd.Timestamp("2026-01-01", tz="UTC")
    else:
        intrabar_df = pd.read_parquet(dl_res["file_path"])
        min_ts = intrabar_df["timestamp"].min()
        max_ts = intrabar_df["timestamp"].max()
        
        gold_path = "data/gold/research_dataset/BTC/4h/research_dataset_with_alpha_scores.parquet"
        if Path(gold_path).exists():
            parent_df = pd.read_parquet(gold_path)
            parent_df["timestamp"] = pd.to_datetime(parent_df["timestamp"])
            if parent_df["timestamp"].dt.tz is None:
                parent_df["timestamp"] = parent_df["timestamp"].dt.tz_localize("UTC")
            parent_df = parent_df[(parent_df["timestamp"] >= min_ts) & (parent_df["timestamp"] <= max_ts)]
        else:
            parent_df = pd.DataFrame({"timestamp": [pd.Timestamp("2026-01-01", tz="UTC")]})
            
    # If we have real signals, we override parent_df to use only those that overlap with intrabar
    if real_signals_df is not None and not dry_run:
        parent_df = real_signals_df[(real_signals_df["timestamp"] >= min_ts) & (real_signals_df["timestamp"] <= max_ts)]
        print(f"Using {len(parent_df)} deduplicated real signals overlapping with intrabar data.")
    elif real_signals_df is not None and dry_run:
         parent_df = real_signals_df.head(1) # Just one for dry run

    # 4. Alignment
    print("Aligning data...")
    align_res = align_intrabar_to_parent(parent_df, intrabar_df, intrabar_tf=timeframe)
    write_intrabar_report(
        f"intrabar_alignment_{v_suffix}",
        {"metrics": align_res["metrics"], "verdict": "INTRABAR_ALIGNMENT_READY"},
        f"Intrabar Alignment {version}",
        ["Verdict: **INTRABAR_ALIGNMENT_READY**"]
    )
    
    # 5. Simulation & 6. MAE/MFE
    print("Simulating and calculating MAE/MFE...")
    sim_results = []
    mae_mfe_results = []
    
    for pt_ts, data in align_res["aligned_data"].items():
        slice_df = data["slice"]
        side = "LONG" # default
        
        # If real signals available, extract side
        if real_signals_df is not None:
            sig_row = parent_df[parent_df["timestamp"] == pt_ts]
            if not sig_row.empty:
                side = sig_row.iloc[0].get("candidate_side", "LONG")

        entry_price = 50000.0
        if not slice_df.empty:
            entry_price = slice_df.iloc[0]["open"]
            
        sim = simulate_intrabar_exit(
            side=side,
            entry_price=entry_price,
            stop_loss=entry_price * 0.95,
            take_profit=entry_price * 1.05,
            entry_time=pt_ts,
            max_exit_time=pt_ts + pd.Timedelta(hours=4),
            intrabar_slice=slice_df
        )
        sim["timestamp"] = pt_ts
        sim_results.append(sim)
        
        mae_mfe = calculate_mae_mfe(side, entry_price, slice_df, entry_price * 0.95)
        mae_mfe_results.append(mae_mfe)
        
    sim_verdict = "INTRABAR_SIGNAL_TIMESTAMP_SIMULATION_PLACEHOLDER" if simulation_input_type != "artificial_placeholder" else "INTRABAR_SIMULATION_PLACEHOLDER"
    
    write_intrabar_report(
        f"intrabar_execution_simulation_{v_suffix}",
        {
            "simulation_input_type": simulation_input_type,
            "is_real_trade_simulation": False,
            "signal_timestamp_source": "ml_predictions" if real_signals_df is not None else "artificial_assumptions",
            "signal_timestamp_type": "real_oos_model_prediction_timestamps" if real_signals_df is not None else "placeholder",
            "trade_parameter_source": "artificial_assumptions",
            "entry_price_source": "intrabar_open",
            "stop_loss_source": "fixed_minus_5pct_placeholder",
            "take_profit_source": "fixed_plus_5pct_placeholder",
            "side_source": "predicted_label_long_only_or_default_long",
            "raw_signal_rows": signal_audit["raw_signal_rows"],
            "unique_signal_timestamps": signal_audit["unique_signal_timestamps"],
            "duplicate_signal_rows": signal_audit["duplicate_signal_rows"],
            "duplicates_per_timestamp_max": signal_audit["duplicates_per_timestamp_max"],
            "models_count": signal_audit["models_count"],
            "selected_signal_policy": signal_audit["selected_signal_policy"],
            "evaluated_signal_count": len(sim_results),
            "artificial_exit_assumptions": True,
            "ambiguous_count": sum(1 for s in sim_results if s["ambiguous"]),
            "verdict": sim_verdict,
            "note": "Timestamps are from ML predictions, but exits are placeholder assumptions."
        },
        f"Intrabar Execution Simulation {version}",
        [f"Verdict: **{sim_verdict}**"]
    )
    
    write_intrabar_report(
        f"intrabar_mae_mfe_{v_suffix}",
        {"mae_mfe_calculated": len(mae_mfe_results)},
        f"Intrabar MAE/MFE {version}",
        ["Verdict: **INTRABAR_MAE_MFE_CALCULATED**"]
    )
    
    # 7. Cost Model
    print("Evaluating cost model...")
    cost_res = evaluate_cost_stress(intrabar_df)
    write_intrabar_report(
        f"intrabar_cost_model_{v_suffix}",
        cost_res,
        f"Intrabar Cost Model {version}",
        [f"Verdict: **{cost_res['verdict']}**"]
    )
    
    # 8. Comparison
    print("Comparing simulations...")
    df_sim_results = pd.DataFrame(sim_results) if sim_results else pd.DataFrame()
    
    from galapagos.research.intrabar.comparison import compare_simulations
    # Pass empty df_4h for now as real 4h backtest results are not easily joinable here yet
    comp_res = compare_simulations(pd.DataFrame(), df_sim_results)
    write_intrabar_report(
        f"intrabar_vs_4h_comparison_{v_suffix}",
        comp_res,
        f"Intrabar vs 4H Comparison {version}",
        [f"Verdict: **{comp_res['verdict']}**"]
    )

    # 10. Main Foundation Report
    found_verdict = "INTRABAR_FOUNDATION_PARTIAL"
    if dl_verdict == "INTRABAR_FETCH_FAILED":
        found_verdict = "INTRABAR_FETCH_FAILED"
    elif dry_run:
        found_verdict = "INTRABAR_FOUNDATION_PARTIAL"
        
    write_intrabar_report(
        f"intrabar_foundation_{v_suffix}",
        {
            "version": version,
            "symbol": symbol,
            "timeframe": timeframe,
            "days": days,
            "dry_run": dry_run,
            "verdict": found_verdict,
            "simulation_ready": False,
            "real_trade_simulation_ready": False,
            "next_required_step": "derive real signal-side/entry/SL/TP policy or pair with trade ledger",
            "simulation_input_type": simulation_input_type,
            "intrabar_sample_rows": len(intrabar_df),
        },
        f"Intrabar Foundation {version}",
        [f"Verdict: **{found_verdict}**"]
    )
    
    # 11. Recommendation
    print("Generating recommendation...")
    rec_payload = {
        "primary_recommendation": "Build real signal/trade ledger interface before judging intrabar exits",
        "ready_for_reviewer": False,
        "holdout_executed": False,
        "no_real_trading": True,
        "simulation_is_placeholder": True,
        "secondary_recommendations": [
            "Do not activate reviewer",
            "Keep ensemble disabled",
            "Do not claim intrabar validates Galapagos exits",
            "Connect to real trade ledger/signals first"
        ]
    }
    
    write_intrabar_report(
        f"{v_suffix}_recommendation",
        rec_payload,
        f"Recommendation {version}",
        [
            f"Verdict: **{rec_payload['primary_recommendation']}**",
            "",
            f"V1.18.2 foundation is **{found_verdict}**.",
            "Simulation is placeholder (artificial exits).",
            "Reviewer remains disabled."
        ]
    )

    print("Orchestration complete.")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", type=str, required=True)
    parser.add_argument("--timeframe", type=str, required=True)
    parser.add_argument("--days", type=int, required=True)
    parser.add_argument("--version", type=str, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    run_orchestrator(args.symbol, args.timeframe, args.days, args.version, args.dry_run)

if __name__ == "__main__":
    main()
