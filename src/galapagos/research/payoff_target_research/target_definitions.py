"""Define exploratory payoff-aware targets."""
from __future__ import annotations

import pandas as pd
import numpy as np

def define_exploratory_targets(frame: pd.DataFrame, *, horizon: str = "forward_return_12bar") -> tuple[pd.DataFrame, dict[str, Any]]:
    """Define new target columns for research."""
    df = frame.copy()
    
    if horizon not in df.columns:
        return df, {"status": "PAYOFF_TARGET_DEFINITIONS_FAILED", "error": f"Horizon {horizon} missing"}
    
    # Ensure cost_proxy exists
    if "cost_proxy" not in df.columns:
        df["cost_proxy"] = 0.001 # Default fallback
        
    ret = pd.to_numeric(df[horizon], errors="coerce")
    cost = pd.to_numeric(df["cost_proxy"], errors="coerce").fillna(0.001)
    net_ret = ret - cost
    
    targets = []
    
    # 1. net_return_regression
    df["target_net_return"] = net_ret
    targets.append({
        "target_name": "net_return_regression",
        "horizon": horizon,
        "label_column_used": "target_net_return",
        "downside_focus_level": "NONE"
    })
    
    # 2. downside_weighted_return
    df["target_downside_weighted"] = np.where(net_ret < 0, net_ret * 2.0, net_ret)
    targets.append({
        "target_name": "downside_weighted_return",
        "horizon": horizon,
        "label_column_used": "target_downside_weighted",
        "downside_focus_level": "MODERATE"
    })
    
    # 3. severe_loss_classifier
    threshold = -0.01
    df["target_severe_loss"] = (net_ret < threshold).astype(int)
    targets.append({
        "target_name": "severe_loss_classifier",
        "horizon": horizon,
        "label_column_used": "target_severe_loss",
        "downside_focus_level": "HIGH",
        "threshold": threshold
    })
    
    # 4. positive_payoff_classifier
    df["target_positive_payoff"] = (net_ret > 0).astype(int)
    targets.append({
        "target_name": "positive_payoff_classifier",
        "horizon": horizon,
        "label_column_used": "target_positive_payoff",
        "downside_focus_level": "NONE"
    })
    
    # 5. payoff_ratio_target
    # Favor asymmetry: net_ret normalized by something stable
    df["target_payoff_ratio"] = net_ret / (net_ret.abs().rolling(100, min_periods=1).mean() + 1e-6)
    targets.append({
        "target_name": "payoff_ratio_target",
        "horizon": horizon,
        "label_column_used": "target_payoff_ratio",
        "downside_focus_level": "ASYMMETRIC"
    })
    
    # 6. ev_gap_target
    if "ev_calibrated_proxy" in df.columns:
        ev_proxy = pd.to_numeric(df["ev_calibrated_proxy"], errors="coerce").fillna(0.0)
        df["target_ev_gap"] = net_ret - ev_proxy
        targets.append({
            "target_name": "ev_gap_target",
            "horizon": horizon,
            "label_column_used": "target_ev_gap",
            "downside_focus_level": "RESIDUAL"
        })
        
    for t in targets:
        t["uses_future_outcome_as_label_only"] = True
        t["used_as_selection_feature"] = False
        t["leakage_policy"] = "LABEL_ONLY_NOT_DECISION_FEATURE"
        t["availability"] = int(df[t["label_column_used"]].notna().sum())
        
        # V1.42.1 Score Policy
        # Since we don't have specific models for these exploratory targets yet,
        # we mark them as label-only diagnostic targets.
        t["score_column_for_evaluation"] = None
        t["score_is_model_output_or_proxy"] = False
        t["target_evaluation_policy"] = "DIAGNOSTIC_LABEL_ONLY_NO_TARGET_SCORE"
        
    return df, {
        "status": "PAYOFF_TARGET_DEFINITIONS_COMPLETE",
        "targets": targets,
        "horizon_used": horizon,
        "target_score_policy": "LABEL_ONLY_DIAGNOSTIC"
    }
