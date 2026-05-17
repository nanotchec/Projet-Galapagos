"""Cost failure analysis.

Analyzes the impact of trading costs (fees + slippage) on the ensemble's edge
and performs sensitivity analysis.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from galapagos.research.failure_analysis.report import write_failure_report


def run_cost_analysis(
    df: pd.DataFrame, version: str, output_dir: str
) -> dict:
    """Analyze cost impact and produce a report."""
    if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    df["year"] = df["timestamp"].dt.year

    # Base cost assumptions used in dataset generation (typically 0.003 for 12bar)
    base_cost = 0.003
    
    cost_data: dict[str, dict[str, Any]] = {}
    
    for year in [2024, 2025, 2026]:
        df_year = df[df["year"] == year]
        if df_year.empty or "forward_return_12bar" not in df_year.columns:
            continue
            
        gross_return = float(df_year["forward_return_12bar"].mean())
        
        # Sensitivity analysis
        sensitivities = {}
        for multiplier in [0.5, 1.0, 2.0, 3.0]:
            cost = base_cost * multiplier
            adj_return = gross_return - cost
            # Fraction of trades where gross was positive but cost made it negative
            positive_gross = df_year[df_year["forward_return_12bar"] > 0]
            destroyed = 0.0
            if not positive_gross.empty:
                destroyed = float((positive_gross["forward_return_12bar"] < cost).mean())
            
            sensitivities[f"x{multiplier}"] = {
                "assumed_cost": cost,
                "adjusted_return": adj_return,
                "positive_after_costs": adj_return > 0,
                "fraction_of_positive_trades_destroyed": destroyed,
            }
            
        cost_data[str(year)] = {
            "gross_forward_return": gross_return,
            "base_cost_adjusted_return": sensitivities["x1.0"]["adjusted_return"],
            "sensitivity": sensitivities,
        }

    verdict = "COST_FAILURE_INCONCLUSIVE"
    if "2026" in cost_data:
        data_26 = cost_data["2026"]
        if data_26["gross_forward_return"] > 0 and data_26["base_cost_adjusted_return"] <= 0:
            verdict = "COSTS_DOMINATE_RECENT_WINDOW"
        elif data_26["gross_forward_return"] <= 0:
            verdict = "EDGE_EXISTS_BEFORE_COSTS_ONLY" if cost_data.get("2024", {}).get("gross_forward_return", 0) > 0 else "NO_EDGE_EVEN_BEFORE_COSTS"

    payload = {
        "version": version,
        "verdict": verdict,
        "cost_analysis": cost_data,
    }

    lines = [
        f"Verdict: **{verdict}**",
        "",
        "### Cost Impact by Year",
    ]
    for y, data in cost_data.items():
        lines.append(f"- **{y}**: Gross = {data['gross_forward_return']:.4f}, Net = {data['base_cost_adjusted_return']:.4f}")

    write_failure_report(
        name=f"cost_failure_{version.replace('.', '_')}",
        payload=payload,
        title=f"Cost Failure Analysis {version}",
        lines=lines,
        output_dir=output_dir,
    )
    return payload
