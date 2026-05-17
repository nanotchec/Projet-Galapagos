from __future__ import annotations

import pandas as pd

from galapagos.data.macro.fred_client import fetch_fred_observations


def parse_fred_observations(series_id: str, observations: list[dict]) -> pd.DataFrame:
    rows = []
    for item in observations:
        value = item.get("value")
        rows.append(
            {
                "timestamp": pd.Timestamp(item.get("date"), tz="UTC"),
                "available_timestamp": pd.Timestamp(item.get("date"), tz="UTC")
                + pd.Timedelta(days=1),
                "source": "fred",
                "series_id": series_id,
                "value": None if value in {None, "."} else float(value),
                "metadata_json": {},
            }
        )
    return pd.DataFrame(rows)


def collect_fred_series(series_ids: list[str], start: str) -> dict:
    outputs = {}
    for series_id in series_ids:
        response = fetch_fred_observations(series_id, start)
        outputs[series_id] = {
            "status": response["status"],
            "rows": len(response.get("observations", [])),
            "data": parse_fred_observations(series_id, response.get("observations", [])),
        }
    return outputs
