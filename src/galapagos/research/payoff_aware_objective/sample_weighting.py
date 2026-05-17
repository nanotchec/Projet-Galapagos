"""Sample weighting helpers for payoff-aware research objectives."""
from __future__ import annotations

import pandas as pd


def build_asymmetric_sample_weights(
    net_return: pd.Series,
    *,
    downside_multiplier: float = 3.0,
) -> pd.Series:
    """Weight negative outcomes more heavily than positive ones."""
    values = pd.to_numeric(net_return, errors="coerce").fillna(0.0)
    weights = pd.Series(1.0, index=values.index, dtype=float)
    negative_mask = values < 0
    weights.loc[negative_mask] = 1.0 + values.loc[negative_mask].abs() * downside_multiplier * 10.0
    return weights.clip(lower=1.0)


def build_downside_sample_weights(
    downside_risk: pd.Series,
    *,
    risk_multiplier: float = 2.0,
) -> pd.Series:
    """Weight rows with larger downside risk more heavily."""
    values = pd.to_numeric(downside_risk, errors="coerce").fillna(0.0)
    weights = 1.0 + values.abs() * risk_multiplier * 10.0
    return pd.Series(weights, index=values.index, dtype=float).clip(lower=1.0)

