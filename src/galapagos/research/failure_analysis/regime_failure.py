"""Regime failure analysis.

Compares market regimes (trend, volatility, etc.) across 2024, 2025, and 2026
to determine if the recent failure is due to a regime shift.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from galapagos.research.failure_analysis.report import write_failure_report


def run_regime_analysis(
    df: pd.DataFrame, version: str, output_dir: str
) -> dict:
    """Analyze the performance by regime and produce a report."""
    if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    df["year"] = df["timestamp"].dt.year
    
    # We will compute pseudo regimes if exact ones are missing
    if "volatility_regime" not in df.columns:
        # Pseudo volatility regime based on rolling std
        if "close" in df.columns:
            rolling_vol = df["close"].pct_change().rolling(30).std()
            median_vol = rolling_vol.median()
            df["volatility_regime"] = "low"
            df.loc[rolling_vol > median_vol, "volatility_regime"] = "high"
        else:
            df["volatility_regime"] = "unknown"

    if "trend_regime" not in df.columns:
        if "close" in df.columns:
            sma_short = df["close"].rolling(10).mean()
            sma_long = df["close"].rolling(50).mean()
            df["trend_regime"] = "range"
            df.loc[sma_short > sma_long * 1.02, "trend_regime"] = "uptrend"
            df.loc[sma_short < sma_long * 0.98, "trend_regime"] = "downtrend"
        else:
            df["trend_regime"] = "unknown"

    regimes_data: dict[str, dict[str, Any]] = {}
    
    for regime_col in ["volatility_regime", "trend_regime"]:
        regimes_data[regime_col] = {}
        for year in [2024, 2025, 2026]:
            df_year = df[df["year"] == year]
            if df_year.empty:
                continue
            
            regimes_data[regime_col][str(year)] = {}
            for regime_val in df_year[regime_col].dropna().unique():
                df_subset = df_year[df_year[regime_col] == regime_val]
                
                mean_12 = float(df_subset["forward_return_12bar"].mean()) if "forward_return_12bar" in df_subset else 0.0
                mean_6 = float(df_subset["forward_return_6bar"].mean()) if "forward_return_6bar" in df_subset else 0.0
                # Fallback: compute hit rate from forward return if binary target is missing
                if "target_up_after_cost_12bar" in df_subset.columns:
                    hit_rate = float(df_subset["target_up_after_cost_12bar"].mean())
                elif "forward_return_12bar" in df_subset.columns:
                    hit_rate = float((df_subset["forward_return_12bar"] > 0.003).mean())
                else:
                    hit_rate = 0.0
                
                regimes_data[regime_col][str(year)][str(regime_val)] = {
                    "count": len(df_subset),
                    "mean_forward_return_12bar": mean_12,
                    "mean_forward_return_6bar": mean_6,
                    "hit_rate_12bar": hit_rate,
                }

    # Simplistic verdict heuristic
    verdict = "REGIME_SHIFT_DETECTED"
    if "trend_regime" in regimes_data and "2026" in regimes_data["trend_regime"]:
        counts_26 = {k: v["count"] for k, v in regimes_data["trend_regime"]["2026"].items()}
        counts_24 = {k: v["count"] for k, v in regimes_data["trend_regime"].get("2024", {}).items()}
        # If distribution of regimes is roughly similar, maybe it's not a regime shift but an overfit
        if set(counts_26.keys()) == set(counts_24.keys()):
            verdict = "REGIME_OVERFIT_SUSPECTED"

    payload = {
        "version": version,
        "verdict": verdict,
        "regime_analysis": regimes_data,
    }

    lines = [
        f"Verdict: **{verdict}**",
        "",
        "### Trend Regime Stats (2026)",
    ]
    if "trend_regime" in regimes_data and "2026" in regimes_data["trend_regime"]:
        for k, v in regimes_data["trend_regime"]["2026"].items():
            lines.append(f"- **{k}**: {v['count']} samples, Mean 12bar: {v['mean_forward_return_12bar']:.4f}")

    write_failure_report(
        name=f"regime_failure_{version.replace('.', '_')}",
        payload=payload,
        title=f"Regime Failure Analysis {version}",
        lines=lines,
        output_dir=output_dir,
    )
    return payload
