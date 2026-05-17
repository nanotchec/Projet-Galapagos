from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any

from galapagos.utils.secrets import get_secret

FRED_BASE_URL = "https://api.stlouisfed.org/fred"


def fred_env_status() -> dict[str, str]:
    return {"FRED_API_KEY": "configured" if get_secret("FRED_API_KEY") else "missing"}


def build_fred_observations_url(series_id: str, start: str, api_key: str) -> str:
    query = urllib.parse.urlencode(
        {
            "series_id": series_id,
            "observation_start": start,
            "api_key": api_key,
            "file_type": "json",
        }
    )
    return f"{FRED_BASE_URL}/series/observations?{query}"


def fetch_fred_observations(
    series_id: str,
    start: str,
    timeout_seconds: int = 15,
) -> dict[str, Any]:
    api_key = get_secret("FRED_API_KEY")
    if not api_key:
        return {"series_id": series_id, "status": "requires_api_key", "observations": []}
    url = build_fred_observations_url(series_id, start, api_key)
    try:
        with urllib.request.urlopen(url, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return {
            "series_id": series_id,
            "status": "available",
            "observations": payload.get("observations", []),
        }
    except Exception as exc:
        return {
            "series_id": series_id,
            "status": "unavailable",
            "error": type(exc).__name__,
            "observations": [],
        }
