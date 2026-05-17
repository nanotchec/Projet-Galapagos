"""Feature drift analysis.

Detects distributional shifts in features (OHLCV, macro, derivatives, alpha scores)
between historical windows (2024, 2025) and the recent window (2026).
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from galapagos.research.failure_analysis.report import write_failure_report


def run_feature_drift_analysis(
    df: pd.DataFrame, version: str, output_dir: str
) -> dict:
    """Analyze feature drift and produce a report."""
    if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    df["year"] = df["timestamp"].dt.year
    
    # Identify feature columns
    exclude_cols = {"timestamp", "year", "target_up_after_cost_6bar", "target_up_after_cost_12bar",
                    "forward_return_6bar", "forward_return_12bar", "forward_return_1bar",
                    "ensemble_probability_6bar_median", "ensemble_probability_12bar_median"}
    feature_cols = [c for c in df.columns if c not in exclude_cols and pd.api.types.is_numeric_dtype(df[c])]
    
    # Simple drift metrics: change in mean normalized by historical std (z-score of mean shift)
    # and change in missing rate
    df_hist = df[df["year"].isin([2024, 2025])]
    df_rec = df[df["year"] == 2026]
    
    drift_data: dict[str, Any] = {}
    
    significant_drifts = 0
    macro_drifts = 0
    deriv_drifts = 0
    
    if not df_hist.empty and not df_rec.empty:
        for col in feature_cols:
            hist_mean = df_hist[col].mean()
            hist_std = df_hist[col].std()
            rec_mean = df_rec[col].mean()
            
            hist_missing = df_hist[col].isna().mean()
            rec_missing = df_rec[col].isna().mean()
            
            z_shift = 0.0
            if pd.notna(hist_std) and hist_std > 0 and pd.notna(rec_mean) and pd.notna(hist_mean):
                z_shift = (rec_mean - hist_mean) / hist_std
                
            missing_delta = rec_missing - hist_missing
            
            is_significant = bool(abs(z_shift) > 1.5 or abs(missing_delta) > 0.2)
            if is_significant:
                significant_drifts += 1
                if "macro_" in col or "fred_" in col:
                    macro_drifts += 1
                elif "funding" in col or "oi" in col or "liquidations" in col or "deriv" in col:
                    deriv_drifts += 1
                    
            drift_data[col] = {
                "hist_mean": float(hist_mean) if pd.notna(hist_mean) else None,
                "rec_mean": float(rec_mean) if pd.notna(rec_mean) else None,
                "z_shift": float(z_shift),
                "missing_delta": float(missing_delta),
                "is_significant": is_significant,
            }

    verdict = "FEATURE_DRIFT_LOW"
    if significant_drifts > len(feature_cols) * 0.2:  # If more than 20% features drifted significantly
        verdict = "FEATURE_DRIFT_DETECTED"
        if deriv_drifts > macro_drifts and deriv_drifts > 5:
            verdict = "DERIVATIVES_COVERAGE_DRIFT"
        elif macro_drifts > deriv_drifts and macro_drifts > 5:
            verdict = "MACRO_FEATURE_DRIFT"

    payload = {
        "version": version,
        "verdict": verdict,
        "features_analyzed": len(feature_cols),
        "significant_drifts": significant_drifts,
        "macro_drifts": macro_drifts,
        "deriv_drifts": deriv_drifts,
        "drift_details": {k: v for k, v in drift_data.items() if v["is_significant"]} # Only store significant ones to save space
    }

    lines = [
        f"Verdict: **{verdict}**",
        "",
        f"Analyzed {len(feature_cols)} features. Found {significant_drifts} significant drifts.",
        f"- Macro drifts: {macro_drifts}",
        f"- Derivatives drifts: {deriv_drifts}",
    ]

    write_failure_report(
        name=f"feature_drift_{version.replace('.', '_')}",
        payload=payload,
        title=f"Feature Drift Analysis {version}",
        lines=lines,
        output_dir=output_dir,
    )
    return payload
