"""Label and target diagnostics.

Evaluates the stability and suitability of the binary classification targets
across different years to identify label base rate shifts or noise.

V1.17.1: If `target_up_after_cost_*` columns are absent, they are synthesised
from `forward_return_*` with a fixed cost threshold so that the analysis can
still run (status=partial).
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from galapagos.research.failure_analysis.report import write_failure_report

_COST_THRESHOLDS = {"6bar": 0.002, "12bar": 0.003}


def run_label_diagnostics(
    df: pd.DataFrame, version: str, output_dir: str
) -> dict:
    """Analyze label base rates and produce a report."""
    if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        df["timestamp"] = pd.to_datetime(df["timestamp"])

    df["year"] = df["timestamp"].dt.year

    targets = [c for c in df.columns if "target_up_after_cost_" in c]

    status = "complete"
    partial_note = ""

    # Fallback: synthesize targets from forward returns if missing
    if not targets:
        for horizon, cost in _COST_THRESHOLDS.items():
            fr_col = f"forward_return_{horizon}"
            tgt_col = f"target_up_after_cost_{horizon}"
            if fr_col in df.columns:
                df[tgt_col] = (df[fr_col] > cost).astype(int)
                targets.append(tgt_col)
        if targets:
            status = "partial"
            partial_note = (
                "target_up_after_cost_* columns were absent. "
                "Synthesised from forward_return with fixed cost thresholds."
            )
        else:
            status = "partial"
            partial_note = "No forward_return columns found to synthesise labels."

    label_data: dict[str, dict[str, Any]] = {}

    for target in targets:
        label_data[target] = {}
        for year in [2024, 2025, 2026]:
            df_year = df[df["year"] == year]
            if df_year.empty:
                continue

            base_rate = float(df_year[target].mean())
            label_data[target][str(year)] = {
                "base_rate": base_rate,
                "count": len(df_year),
            }

    verdict = "LABELS_STABLE"

    # Check for base rate shifts in the 12bar target
    target_12 = "target_up_after_cost_12bar"
    if target_12 in label_data and "2026" in label_data[target_12] and "2024" in label_data[target_12]:
        rate_26 = label_data[target_12]["2026"]["base_rate"]
        rate_24 = label_data[target_12]["2024"]["base_rate"]

        if rate_26 < 0.40 and rate_24 > 0.50:
            verdict = "LABEL_BASE_RATE_SHIFT"
        elif rate_26 < 0.30:
            verdict = "LABEL_COST_THRESHOLD_TOO_HIGH"

    payload: dict[str, Any] = {
        "version": version,
        "status": status,
        "verdict": verdict,
        "label_analysis": label_data,
    }
    if partial_note:
        payload["partial_note"] = partial_note

    lines = [
        f"Verdict: **{verdict}**",
        f"Status: {status}",
        "",
    ]
    if partial_note:
        lines.append(f"> {partial_note}")
        lines.append("")
    lines.append("### Label Base Rates by Year")
    for target, years in label_data.items():
        lines.append(f"**{target}**")
        for y, stats in years.items():
            lines.append(f"- {y}: {stats['base_rate']:.2%}")

    write_failure_report(
        name=f"label_diagnostics_{version.replace('.', '_')}",
        payload=payload,
        title=f"Label Diagnostics {version}",
        lines=lines,
        output_dir=output_dir,
    )
    return payload
