"""Cost threshold utilities for signal selection."""
from __future__ import annotations

import numpy as np
import pandas as pd

DEFAULT_COST_PCT = 0.003


def safe_cost_pct(frame: pd.DataFrame, default: float = DEFAULT_COST_PCT) -> pd.Series:
    if "cost_pct" in frame.columns:
        return pd.to_numeric(frame["cost_pct"], errors="coerce").fillna(default)
    if "cost_proxy_pct" in frame.columns:
        return pd.to_numeric(frame["cost_proxy_pct"], errors="coerce").fillna(default)
    return pd.Series(default, index=frame.index, dtype=float)


def cost_viability_flags(
    expected_move: pd.Series,
    cost: pd.Series,
    multiplier: float = 1.0,
) -> pd.Series:
    expected = pd.to_numeric(expected_move, errors="coerce").fillna(0.0)
    costs = pd.to_numeric(cost, errors="coerce").fillna(DEFAULT_COST_PCT)
    return expected > multiplier * costs


def cost_to_move_ratio(expected_move: pd.Series, cost: pd.Series) -> pd.Series:
    expected = pd.to_numeric(expected_move, errors="coerce").abs()
    costs = pd.to_numeric(cost, errors="coerce").fillna(DEFAULT_COST_PCT)
    return costs / expected.replace(0.0, np.nan)
