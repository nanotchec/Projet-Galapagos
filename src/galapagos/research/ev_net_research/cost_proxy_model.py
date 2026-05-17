from __future__ import annotations

import pandas as pd


def apply_cost_proxy(df: pd.DataFrame, fixed_bps: float = 10.0) -> pd.DataFrame:
    """
    Apply a cost proxy (bps) to each signal.
    """
    # 10 bps = 0.001
    df["cost_proxy"] = fixed_bps / 10000.0
    return df
