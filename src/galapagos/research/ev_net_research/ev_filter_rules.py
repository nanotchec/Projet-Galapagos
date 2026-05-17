from __future__ import annotations

from typing import Any

import pandas as pd


def apply_ev_filter_rules(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply various exploratory EV filter rules.
    """
    ready = df.get("ev_proxy_ready", False)
    
    # 1. Basic: EV > 0
    df["filter_ev_gt_0"] = (ready) & (df["ev_calibrated_proxy"] > 0)
    
    # 2. Buffer: EV > Cost
    df["filter_ev_gt_cost_buffer"] = (ready) & (df["ev_calibrated_proxy"] > df["cost_proxy"])
    
    # 3. Prob threshold + Positive EV
    df["filter_prob_65_ev_pos"] = (
        (ready) & 
        (df["predicted_probability_calibrated"] >= 0.65) & 
        (df["ev_calibrated_proxy"] > 0)
    )
    
    # 4. Top quantile (NON-CAUSAL, for audit only)
    df["filter_ev_top_quantile_non_causal"] = (
        (ready) & 
        (df["ev_calibrated_proxy"] > df["ev_calibrated_proxy"].quantile(0.9))
    )
    
    # 5. Causal Top Quantile
    df["filter_ev_top_quantile_causal"] = (
        (ready) & 
        (df["ev_calibrated_proxy"] > (
            df["ev_calibrated_proxy"].shift(1).expanding(min_periods=1000).quantile(0.9)
        ))
    )
    
    return df


def get_ev_filter_definitions() -> list[dict[str, Any]]:
    """
    Get metadata for all exploratory EV filters.
    """
    return [
        {
            "filter_name": "filter_ev_gt_0",
            "family": "EV_BASIC",
            "description": "Net Expected Value > 0",
            "causal_status": "CAUSAL_PAST_PAYOFFS",
            "eligible_for_ranking": True,
            "exclusion_reason": None,
            "uses_future_info": False,
            "uses_full_period_statistic": False,
            "requires_warmup": True,
            "selection_columns_used": ["ev_calibrated_proxy"]
        },
        {
            "filter_name": "filter_ev_gt_cost_buffer",
            "family": "EV_BUFFERED",
            "description": "Net Expected Value > 10bps Cost Proxy",
            "causal_status": "CAUSAL_PAST_PAYOFFS",
            "eligible_for_ranking": True,
            "exclusion_reason": None,
            "uses_future_info": False,
            "uses_full_period_statistic": False,
            "requires_warmup": True,
            "selection_columns_used": ["ev_calibrated_proxy", "cost_proxy"]
        },
        {
            "filter_name": "filter_prob_65_ev_pos",
            "family": "PROB_EV_HYBRID",
            "description": "Calibrated Prob >= 0.65 AND Net EV > 0",
            "causal_status": "CAUSAL_HYBRID",
            "eligible_for_ranking": True,
            "exclusion_reason": None,
            "uses_future_info": False,
            "uses_full_period_statistic": False,
            "requires_warmup": True,
            "selection_columns_used": ["predicted_probability_calibrated", "ev_calibrated_proxy"]
        },
        {
            "filter_name": "filter_ev_top_quantile_non_causal",
            "family": "EV_QUANTILE",
            "description": "Top 10% EV (Full Period Quantile)",
            "causal_status": "RETROSPECTIVE_ONLY_FULL_PERIOD_QUANTILE",
            "eligible_for_ranking": False,
            "exclusion_reason": "full_period_quantile_non_causal",
            "uses_future_info": True,
            "uses_full_period_statistic": True,
            "requires_warmup": False,
            "selection_columns_used": ["ev_calibrated_proxy"]
        },
        {
            "filter_name": "filter_ev_top_quantile_causal",
            "family": "EV_QUANTILE",
            "description": "Top 10% EV (Expanding Past Quantile)",
            "causal_status": "CAUSAL_EXPANDING_PAST_QUANTILE",
            "eligible_for_ranking": True,
            "exclusion_reason": None,
            "uses_future_info": False,
            "uses_full_period_statistic": False,
            "requires_warmup": True,
            "selection_columns_used": ["ev_calibrated_proxy"]
        }
    ]
