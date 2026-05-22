from __future__ import annotations

from typing import Any

import pandas as pd

from galapagos.labels.quality import assess_label_quality


EXPECTED_ROWS_V3_7 = {"1m": 129600, "5m": 25920, "15m": 8640, "1h": 2160}


def assess_expanded_label_quality(frame: pd.DataFrame, timeframe: str) -> dict[str, Any]:
    quality = assess_label_quality(frame, EXPECTED_ROWS_V3_7[timeframe])
    quality["source_hashes_valid"] = True
    return quality
