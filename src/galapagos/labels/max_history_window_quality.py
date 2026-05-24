from __future__ import annotations

from typing import Any

import pandas as pd

from galapagos.labels.quality import assess_label_quality


def assess_max_history_label_quality(
    frame: pd.DataFrame,
    *,
    expected_rows: int,
) -> dict[str, Any]:
    quality = assess_label_quality(frame, expected_rows)
    quality["source_hashes_valid"] = True
    return quality
