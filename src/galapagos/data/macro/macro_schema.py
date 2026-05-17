from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class MacroRecord:
    timestamp: str
    available_timestamp: str
    source: str
    series_id: str
    value: float | None
    metadata_json: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
