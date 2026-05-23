from __future__ import annotations

from typing import Any

import pandas as pd

from galapagos.features.quality import assess_feature_quality


EXPECTED_ROWS_V4_3 = {"1m": 527040, "5m": 105408, "15m": 35136, "1h": 8784}


def assess_one_year_feature_quality(frame: pd.DataFrame, timeframe: str) -> dict[str, Any]:
    quality = assess_feature_quality(frame, EXPECTED_ROWS_V4_3[timeframe], timeframe)
    if quality["warmup_rows"] != 30:
        quality["errors"].append(f"{timeframe} features warmup rows mismatch: got {quality['warmup_rows']}, expected 30")
    return quality
