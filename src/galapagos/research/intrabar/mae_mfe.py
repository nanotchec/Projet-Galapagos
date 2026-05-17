"""Calculate Maximum Adverse and Favorable Excursions (MAE/MFE) using intrabar data."""
from __future__ import annotations

from typing import Any

import pandas as pd


def calculate_mae_mfe(
    side: str, entry_price: float, intrabar_slice: pd.DataFrame, stop_loss: float = 0.0
) -> dict[str, Any]:
    """Calculate exact MAE/MFE on intrabar data."""
    if intrabar_slice.empty:
        return {
            "max_favorable_excursion_abs": 0.0,
            "max_favorable_excursion_pct": 0.0,
            "max_adverse_excursion_abs": 0.0,
            "max_adverse_excursion_pct": 0.0,
            "time_to_mfe": 0,
            "time_to_mae": 0,
            "path_efficiency": 0.0,
            "stop_too_tight_flag": False,
            "status": "missing_intrabar",
        }

    max_high = intrabar_slice["high"].max()
    min_low = intrabar_slice["low"].min()

    # We want to know time to MFE/MAE (in bars)
    max_high_idx = intrabar_slice["high"].idxmax()
    min_low_idx = intrabar_slice["low"].idxmin()

    # Convert index difference to integer steps
    try:
        time_to_high = intrabar_slice.index.get_loc(max_high_idx)
    except Exception:
        time_to_high = 0

    try:
        time_to_low = intrabar_slice.index.get_loc(min_low_idx)
    except Exception:
        time_to_low = 0

    if side == "LONG":
        mfe_abs = max_high - entry_price
        mfe_pct = mfe_abs / entry_price
        mae_abs = entry_price - min_low
        mae_pct = mae_abs / entry_price

        time_to_mfe = time_to_high
        time_to_mae = time_to_low

        stop_too_tight = (min_low <= stop_loss) if stop_loss > 0 else False

    else:  # SHORT
        mfe_abs = entry_price - min_low
        mfe_pct = mfe_abs / entry_price
        mae_abs = max_high - entry_price
        mae_pct = mae_abs / entry_price

        time_to_mfe = time_to_low
        time_to_mae = time_to_high

        stop_too_tight = (max_high >= stop_loss) if stop_loss > 0 else False

    path_eff = mfe_pct / mae_pct if mae_pct > 0 else 999.0

    return {
        "max_favorable_excursion_abs": float(mfe_abs),
        "max_favorable_excursion_pct": float(mfe_pct),
        "max_adverse_excursion_abs": float(mae_abs),
        "max_adverse_excursion_pct": float(mae_pct),
        "time_to_mfe": int(time_to_mfe),
        "time_to_mae": int(time_to_mae),
        "path_efficiency": float(path_eff),
        "stop_too_tight_flag": stop_too_tight,
        "status": "complete",
    }
