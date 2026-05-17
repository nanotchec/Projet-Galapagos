"""Data gap analysis.

Identifies missing critical data sets (intrabar, full orderbook, liquidations)
that could explain the model's inability to find a robust edge in recent regimes.
"""
from __future__ import annotations

import pandas as pd

from galapagos.research.failure_analysis.report import write_failure_report


def run_data_gap_analysis(
    df: pd.DataFrame, version: str, output_dir: str
) -> dict:
    """Analyze data gaps and produce a report."""
    
    # We look at the columns to see what's missing
    cols = df.columns.tolist()
    
    has_intrabar = any("intrabar" in c.lower() for c in cols)
    has_liquidations = any("liquidation" in c.lower() for c in cols)
    has_oi = any("open_interest" in c.lower() or "oi" in c.lower().split("_") for c in cols)
    
    gap_data = {
        "intrabar_available": has_intrabar,
        "liquidations_available": has_liquidations,
        "oi_available": has_oi,
        "coinglass_integrated": False,  # Known constraint
        "macro_coverage_good": any("fred" in c.lower() for c in cols),
    }

    verdict = "PUBLIC_DATA_STILL_ENOUGH"
    if not has_intrabar:
        verdict = "INTRABAR_DATA_PRIORITY"
    elif not has_liquidations:
        verdict = "LIQUIDATIONS_PROVIDER_NEEDED"
    elif not has_oi:
        verdict = "OI_MULTI_EXCHANGE_PROVIDER_NEEDED"

    payload = {
        "version": version,
        "verdict": verdict,
        "data_gaps": gap_data,
    }

    lines = [
        f"Verdict: **{verdict}**",
        "",
        "### Data Availability",
        f"- Intrabar: {has_intrabar}",
        f"- Liquidations: {has_liquidations}",
        f"- Open Interest: {has_oi}",
    ]

    write_failure_report(
        name=f"data_gap_analysis_{version.replace('.', '_')}",
        payload=payload,
        title=f"Data Gap Analysis {version}",
        lines=lines,
        output_dir=output_dir,
    )
    return payload
