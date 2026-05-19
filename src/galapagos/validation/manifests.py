from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require_fields(payload: dict[str, Any], fields: list[str], *, prefix: str = "") -> list[str]:
    errors: list[str] = []
    for field in fields:
        if field not in payload:
            errors.append(f"{prefix}{field} missing")
    return errors
