from __future__ import annotations

from typing import Any

import pandas as pd

from galapagos.features.quality import assess_feature_quality


def assess_max_history_feature_quality(
    frame: pd.DataFrame,
    timeframe: str,
    *,
    expected_rows: int,
) -> dict[str, Any]:
    quality = assess_feature_quality(frame, expected_rows, timeframe)
    if quality["warmup_rows"] != 30:
        quality["errors"].append(
            f"{timeframe} features warmup rows mismatch: got {quality['warmup_rows']}, expected 30"
        )
    return quality
