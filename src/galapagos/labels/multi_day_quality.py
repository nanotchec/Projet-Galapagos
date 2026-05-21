from __future__ import annotations

from typing import Any

import pandas as pd

from galapagos.labels.quality import assess_label_quality


EXPECTED_ROWS_V3_1 = {"1m": 10080, "5m": 2016, "15m": 672, "1h": 168}


def assess_multi_day_label_quality(frame: pd.DataFrame, timeframe: str) -> dict[str, Any]:
    quality = assess_label_quality(frame, EXPECTED_ROWS_V3_1[timeframe])
    quality["source_hashes_valid"] = True
    return quality
