from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class DerivativesRecord:
    timestamp: str
    available_timestamp: str
    source: str
    symbol: str
    metric_name: str
    metric_value: float | None
    metadata_json: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


REQUIRED_COLUMNS = [
    "timestamp",
    "available_timestamp",
    "source",
    "symbol",
    "metric_name",
    "metric_value",
    "metadata_json",
]
