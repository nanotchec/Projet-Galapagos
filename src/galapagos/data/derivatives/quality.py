from __future__ import annotations

import pandas as pd


def derivatives_quality(records: pd.DataFrame) -> dict:
    if records.empty:
        return {"status": "unavailable", "rows": 0, "metrics": []}
    return {
        "status": "available",
        "rows": int(len(records)),
        "metrics": sorted(records["metric_name"].dropna().unique().tolist()),
        "start_timestamp": str(records["timestamp"].min()),
        "end_timestamp": str(records["timestamp"].max()),
    }
