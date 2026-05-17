"""Label construction for payoff-aware objective research."""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def build_payoff_labels(frame: pd.DataFrame, *, default_cost_pct: float = 0.001) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Build exploratory payoff labels from future outcomes.

    Future outcomes are used only as labels, never as features.
    """
    data = frame.copy()
    data["forward_return_12bar"] = pd.to_numeric(data["forward_return_12bar"], errors="coerce")
    if "cost_proxy" in data.columns:
        cost_proxy = pd.to_numeric(data["cost_proxy"], errors="coerce").fillna(default_cost_pct)
    else:
        cost_proxy = pd.Series(default_cost_pct, index=data.index, dtype="float64")
    data["cost_proxy"] = cost_proxy
    data["net_return_label"] = data["forward_return_12bar"] - data["cost_proxy"]
    data["signed_payoff_label"] = (data["net_return_label"] > 0).astype(int)
    data["asymmetric_payoff_label"] = np.where(
        data["net_return_label"] < 0,
        data["net_return_label"].abs() * 2.0,
        data["net_return_label"].clip(lower=0.0),
    )
    data["downside_risk_label"] = np.where(data["net_return_label"] < 0, data["net_return_label"].abs(), 0.0)
    if "ev_calibrated_proxy" in data.columns:
        ev_proxy = pd.to_numeric(data["ev_calibrated_proxy"], errors="coerce")
    else:
        ev_proxy = pd.Series(0.0, index=data.index, dtype="float64")
    data["ev_gap_label"] = data["net_return_label"] - ev_proxy
    report = {
        "targets_defined": [
            "net_return_regression_target",
            "signed_payoff_classification_target",
            "asymmetric_payoff_weighted_target",
            "downside_risk_target",
            "ev_realization_gap_target",
        ],
        "target_columns_used": {
            "net_return_regression_target": ["forward_return_12bar", "cost_proxy"],
            "signed_payoff_classification_target": ["forward_return_12bar", "cost_proxy"],
            "asymmetric_payoff_weighted_target": ["forward_return_12bar", "cost_proxy"],
            "downside_risk_target": ["forward_return_12bar", "cost_proxy"],
            "ev_realization_gap_target": ["forward_return_12bar", "cost_proxy", "ev_calibrated_proxy"],
        },
        "target_availability": {
            "net_return_regression_target": int(data["net_return_label"].notna().sum()),
            "signed_payoff_classification_target": int(data["signed_payoff_label"].notna().sum()),
            "asymmetric_payoff_weighted_target": int(data["asymmetric_payoff_label"].notna().sum()),
            "downside_risk_target": int(data["downside_risk_label"].notna().sum()),
            "ev_realization_gap_target": int(data["ev_gap_label"].notna().sum()),
        },
        "future_outcomes_used_only_as_training_labels": True,
        "targets_not_available_at_decision_time": True,
        "target_leakage_policy": "LABEL_ONLY_NOT_SELECTION_FEATURE",
        "payoff_target_status": "PAYOFF_OBJECTIVE_TARGETS_DEFINED_LABEL_ONLY",
    }
    return data, report
