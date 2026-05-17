"""Recent window failure analysis.

Analyzes the most recent window (e.g., 2026) vs historical windows (2024, 2025)
to confirm and characterize the failure.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from galapagos.research.failure_analysis.report import write_failure_report


def run_recent_window_analysis(
    df: pd.DataFrame, ensemble_report: dict, version: str, output_dir: str
) -> dict:
    """Analyze the recent window vs history and produce a report."""
    # Ensure datetime
    if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        df["timestamp"] = pd.to_datetime(df["timestamp"])

    df["year"] = df["timestamp"].dt.year
    df_history = df[df["year"].isin([2024, 2025])]
    df_recent = df[df["year"] == 2026]

    # Handle case where dataset might not have 2026
    if df_recent.empty:
        payload = {"status": "missing_recent_data", "verdict": "RECENT_FAILURE_INCONCLUSIVE"}
        write_failure_report(
            name=f"recent_window_failure_{version.replace('.', '_')}",
            payload=payload,
            title=f"Recent Window Failure Analysis {version}",
            lines=["Missing recent data (2026)."],
            output_dir=output_dir,
        )
        return payload

    # Basic stats
    def get_stats(data: pd.DataFrame) -> dict[str, Any]:
        return {
            "mean_btc_return": float(data["close"].pct_change().mean() * 100) if "close" in data else 0.0,
            "volatility": float(data["close"].pct_change().std() * 100) if "close" in data else 0.0,
            "signal_count": len(data),
            "top_bucket_rate": float((data["ensemble_probability_12bar_median"] > 0.8).mean()) 
                if "ensemble_probability_12bar_median" in data else 0.0,
        }

    hist_stats = get_stats(df_history)
    rec_stats = get_stats(df_recent)

    # Retrieve 12bar results from ensemble report
    horizon_results = ensemble_report.get("results_by_horizon", {}).get("12bar", {}).get("window_results", {})
    hist_return = 0.0
    rec_return = 0.0
    if "2024" in horizon_results and "2025" in horizon_results:
        hist_return = (horizon_results["2024"].get("mean_cost_adjusted_forward_return", 0) + 
                       horizon_results["2025"].get("mean_cost_adjusted_forward_return", 0)) / 2.0
    if "2026" in horizon_results:
        rec_return = horizon_results["2026"].get("mean_cost_adjusted_forward_return", 0)

    verdict = "RECENT_FAILURE_CONFIRMED"
    if rec_return >= 0:
        verdict = "RECENT_FAILURE_INCONCLUSIVE"
    elif rec_stats["volatility"] > hist_stats["volatility"] * 1.5:
        verdict = "RECENT_FAILURE_REGIME_DRIVEN"

    payload = {
        "version": version,
        "verdict": verdict,
        "historical_stats": hist_stats,
        "recent_stats": rec_stats,
        "historical_mean_edge": hist_return,
        "recent_mean_edge": rec_return,
        "edge_degradation": float(rec_return - hist_return)
    }

    lines = [
        f"Verdict: **{verdict}**",
        "",
        "### Historical vs Recent Stats",
        f"- Historical Volatility: {hist_stats['volatility']:.2f}%",
        f"- Recent Volatility: {rec_stats['volatility']:.2f}%",
        f"- Historical Edge (12bar): {hist_return:.4f}",
        f"- Recent Edge (12bar): {rec_return:.4f}",
    ]

    write_failure_report(
        name=f"recent_window_failure_{version.replace('.', '_')}",
        payload=payload,
        title=f"Recent Window Failure Analysis {version}",
        lines=lines,
        output_dir=output_dir,
    )
    return payload
