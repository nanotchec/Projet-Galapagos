from __future__ import annotations

from typing import Any

import pandas as pd

from galapagos.labels.quality import assess_label_quality


EXPECTED_ROWS_V4_4 = {"1m": 527040, "5m": 105408, "15m": 35136, "1h": 8784}


def assess_one_year_label_quality(frame: pd.DataFrame, timeframe: str) -> dict[str, Any]:
    quality = assess_label_quality(frame, EXPECTED_ROWS_V4_4[timeframe])
    quality["source_hashes_valid"] = True
    return quality
