from __future__ import annotations

import pandas as pd


def macro_quality(records: pd.DataFrame) -> dict:
    if records.empty:
        return {"status": "requires_api_key_or_unavailable", "rows": 0, "series": []}
    return {
        "status": "available",
        "rows": int(len(records)),
        "series": sorted(records["series_id"].dropna().unique().tolist()),
        "start_timestamp": str(records["timestamp"].min()),
        "end_timestamp": str(records["timestamp"].max()),
    }
