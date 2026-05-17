"""Horizon diagnostics.

Evaluates alternative forward return horizons (1bar, 3bar, 24bar) against
the standard 6bar and 12bar to see if signal decay or mismatch is responsible
for the failure.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from galapagos.research.failure_analysis.report import write_failure_report


def run_horizon_diagnostics(
    df: pd.DataFrame, version: str, output_dir: str
) -> dict:
    """Analyze different horizons and produce a report."""
    if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    df["year"] = df["timestamp"].dt.year
    
    horizons = ["1bar", "3bar", "6bar", "12bar", "24bar"]
    horizon_cols = [f"forward_return_{h}" for h in horizons if f"forward_return_{h}" in df.columns]
    
    horizon_data: dict[str, dict[str, Any]] = {}
    
    # Analyze by year
    for year in [2024, 2025, 2026]:
        df_year = df[df["year"] == year]
        if df_year.empty:
            continue
            
        horizon_data[str(year)] = {}
        for col in horizon_cols:
            horizon = col.split("_")[-1]
            mean_ret = float(df_year[col].mean())
            hit_rate = float((df_year[col] > 0).mean())
            # Simplistic cost adj
            cost = 0.003
            if horizon == "6bar":
                cost = 0.002
            elif horizon in ["1bar", "3bar"]:
                cost = 0.001
            elif horizon == "24bar":
                cost = 0.004
                
            horizon_data[str(year)][horizon] = {
                "mean_return": mean_ret,
                "hit_rate_gross": hit_rate,
                "mean_cost_adj_return": mean_ret - cost,
                "assumed_cost": cost,
            }

    verdict = "HORIZON_ANALYSIS_INCONCLUSIVE"
    
    if "2026" in horizon_data:
        data_26 = horizon_data["2026"]
        best_horizon = None
        best_ret = -float("inf")
        for h, stats in data_26.items():
            if stats["mean_cost_adj_return"] > best_ret:
                best_ret = stats["mean_cost_adj_return"]
                best_horizon = h
                
        if best_horizon in ["1bar", "3bar"] and best_ret > 0:
            verdict = "SHORTER_HORIZON_CANDIDATE"
        elif best_horizon == "24bar" and best_ret > 0:
            verdict = "LONGER_HORIZON_CANDIDATE"
        elif data_26.get("12bar", {}).get("mean_cost_adj_return", 0) <= 0:
            verdict = "HORIZON_12BAR_WEAK"

    payload = {
        "version": version,
        "verdict": verdict,
        "horizon_analysis": horizon_data,
    }

    lines = [
        f"Verdict: **{verdict}**",
        "",
        "### Cost-Adjusted Returns by Horizon",
    ]
    for year, h_data in horizon_data.items():
        lines.append(f"**{year}**")
        for h, stats in h_data.items():
            lines.append(f"- {h}: {stats['mean_cost_adj_return']:.4f} (Gross: {stats['mean_return']:.4f})")

    write_failure_report(
        name=f"horizon_diagnostics_{version.replace('.', '_')}",
        payload=payload,
        title=f"Horizon Diagnostics {version}",
        lines=lines,
        output_dir=output_dir,
    )
    return payload
