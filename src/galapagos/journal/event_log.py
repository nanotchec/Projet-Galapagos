from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def system_event(level: str, message: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "level": level,
        "message": message,
        "payload": payload or {},
    }

