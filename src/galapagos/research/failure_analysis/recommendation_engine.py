"""Recommendation engine.

Synthesizes the verdicts from all failure analysis modules to produce a
final, actionable recommendation.
"""
from __future__ import annotations

from typing import Any

from galapagos.research.failure_analysis.report import write_failure_report


def run_recommendation_engine(
    verdicts: dict[str, str], version: str, output_dir: str
) -> dict:
    """Synthesize verdicts into a final recommendation."""
    v_suffix = version.replace(".", "_")

    primary_recommendation = "I. Pause trading-agent path and focus on research"
    secondary_recommendations: list[str] = []
    do_not_do_next = [
        "G. Do not activate LLM reviewer",
        "Do not enable real trading",
        "Do not execute holdout",
    ]

    # Simple rule engine
    if verdicts.get("data_gap_analysis") == "INTRABAR_DATA_PRIORITY":
        primary_recommendation = "B. Add intrabar data first"
        secondary_recommendations.append("A. Improve features first")
    elif verdicts.get("feature_drift") in ["DERIVATIVES_COVERAGE_DRIFT", "MACRO_FEATURE_DRIFT"]:
        primary_recommendation = "A. Improve features first"
    elif verdicts.get("cost_failure") == "COSTS_DOMINATE_RECENT_WINDOW":
        primary_recommendation = "B. Add intrabar data first"  # To manage slippage/costs better
    elif verdicts.get("label_diagnostics") in ["LABEL_BASE_RATE_SHIFT", "LABEL_COST_THRESHOLD_TOO_HIGH"]:
        primary_recommendation = "D. Redesign labels/horizons"
    elif verdicts.get("regime_failure") == "REGIME_SHIFT_DETECTED":
        primary_recommendation = "F. Try model ensemble again with stricter regime filter"
    elif verdicts.get("data_gap_analysis") in ["LIQUIDATIONS_PROVIDER_NEEDED", "OI_MULTI_EXCHANGE_PROVIDER_NEEDED"]:
        primary_recommendation = "H. Provider data review needed"
        secondary_recommendations.append("C. Improve derivatives data first")

    rationale = f"Based on verdicts: {verdicts}"

    payload: dict[str, Any] = {
        "version": version,
        "primary_recommendation": primary_recommendation,
        "secondary_recommendations": secondary_recommendations,
        "do_not_do_next": do_not_do_next,
        "rationale": rationale,
        "ready_for_reviewer": False,
        "required_before_llm_reviewer": "A robust ensemble signal across all regimes.",
        "required_before_holdout": "LLM reviewer success and robust ML signal.",
        "required_before_live_paper_autonomy": "Holdout success.",
        "verdicts_used": verdicts,
    }

    lines = [
        f"## Primary Recommendation: **{primary_recommendation}**",
        "",
        "### Secondary Recommendations",
        *[f"- {r}" for r in secondary_recommendations],
        "",
        "### Do Not Do Next",
        *[f"- {r}" for r in do_not_do_next],
        "",
        "### Rationale",
        rationale,
    ]

    write_failure_report(
        name=f"{v_suffix}_recommendation",
        payload=payload,
        title=f"{version} Recommendation",
        lines=lines,
        output_dir=output_dir,
    )
    return payload
