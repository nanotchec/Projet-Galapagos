from __future__ import annotations

from typing import Any

import pandas as pd


def assess_ohlcv_quality(df: pd.DataFrame) -> dict[str, Any]:
    missing = int(df[["open", "high", "low", "close", "volume"]].isna().sum().sum())
    return {
        "ohlcv_rows": int(len(df)),
        "missing_values": missing,
        "status": "available" if len(df) > 0 and missing == 0 else "degraded",
    }

