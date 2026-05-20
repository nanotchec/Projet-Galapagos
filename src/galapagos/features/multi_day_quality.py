from __future__ import annotations

from typing import Any

import pandas as pd

from galapagos.features.quality import assess_feature_quality


EXPECTED_ROWS_V3_0 = {"1m": 10080, "5m": 2016, "15m": 672, "1h": 168}


def assess_multi_day_feature_quality(frame: pd.DataFrame, timeframe: str) -> dict[str, Any]:
    return assess_feature_quality(frame, EXPECTED_ROWS_V3_0[timeframe], timeframe)
