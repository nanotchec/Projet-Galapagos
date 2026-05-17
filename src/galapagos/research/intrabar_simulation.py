from __future__ import annotations

import pandas as pd


def align_signal_to_intrabar_window(
    signal_timestamp: str,
    intrabar_data: pd.DataFrame,
) -> pd.DataFrame:
    timestamps = pd.to_datetime(intrabar_data["timestamp"])
    return intrabar_data[timestamps >= pd.Timestamp(signal_timestamp)].copy()


def simulate_tp_sl_intrabar(*args, **kwargs) -> dict:
    return {
        "status": "not_implemented_v1_11_design_only",
        "reason": "Intrabar execution simulation is documented but not active in V1.11.",
    }


def validate_intrabar_coverage(signal_data: pd.DataFrame, intrabar_data: pd.DataFrame) -> dict:
    return {
        "signals": len(signal_data),
        "intrabar_rows": len(intrabar_data),
        "coverage_available": not signal_data.empty and not intrabar_data.empty,
    }
