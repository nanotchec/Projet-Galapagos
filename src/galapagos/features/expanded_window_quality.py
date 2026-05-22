from __future__ import annotations

from typing import Any

import pandas as pd

from galapagos.features.quality import assess_feature_quality


EXPECTED_ROWS_V3_6 = {"1m": 129600, "5m": 25920, "15m": 8640, "1h": 2160}


def assess_expanded_feature_quality(frame: pd.DataFrame, timeframe: str) -> dict[str, Any]:
    quality = assess_feature_quality(frame, EXPECTED_ROWS_V3_6[timeframe], timeframe)
    if quality["warmup_rows"] != 30:
        quality["errors"].append(f"{timeframe} features warmup rows mismatch: got {quality['warmup_rows']}, expected 30")
    return quality
