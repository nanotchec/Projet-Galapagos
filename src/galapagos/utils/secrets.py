from __future__ import annotations

import os


def get_secret(name: str) -> str | None:
    value = os.getenv(name)
    return value if value else None


def redact_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "***redacted***"
    return f"{value[:2]}***redacted***{value[-2:]}"


def safe_env_status(names: list[str]) -> dict[str, str]:
    return {name: "configured" if get_secret(name) else "missing" for name in names}
