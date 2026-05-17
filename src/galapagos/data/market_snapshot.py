from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from galapagos.utils.time_utils import utc_now_iso


@dataclass
class MarketSnapshot:
    profile: str
    asset: str
    timeframe: str
    market: dict[str, Any]
    indicators: dict[str, Any]
    derivatives: dict[str, Any]
    scenarios: list[dict[str, Any]]
    data_quality: dict[str, Any]
    timestamp_utc: str = field(default_factory=utc_now_iso)
    collected_at_utc: str = field(default_factory=utc_now_iso)
    source_timestamps: dict[str, Any] = field(default_factory=dict)
    data_mode: str = "mock"
    data_freshness_seconds: float | None = None
    derivatives_availability_summary: dict[str, str] = field(default_factory=dict)
    unavailable_features: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp_utc": self.timestamp_utc,
            "collected_at_utc": self.collected_at_utc,
            "profile": self.profile,
            "asset": self.asset,
            "timeframe": self.timeframe,
            "market": self.market,
            "indicators": self.indicators,
            "derivatives": self.derivatives,
            "scenarios": self.scenarios,
            "data_quality": self.data_quality,
            "source_timestamps": self.source_timestamps,
            "data_mode": self.data_mode,
            "data_freshness_seconds": self.data_freshness_seconds,
            "derivatives_availability_summary": self.derivatives_availability_summary,
            "unavailable_features": self.unavailable_features,
        }

    def content_hash(self) -> str:
        payload = json.dumps(self.to_dict(), sort_keys=True, default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
