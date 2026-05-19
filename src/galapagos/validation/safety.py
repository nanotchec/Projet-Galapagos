from __future__ import annotations

from pathlib import Path
from typing import Any


EXPECTED_FALSE_FLAGS = [
    "authentication_used",
    "api_key_used",
    "private_endpoint_used",
    "orders_enabled",
    "paper_live_enabled",
    "trading_enabled",
    "ml_enabled",
    "labels_enabled",
    "backtest_enabled",
]

EXPECTED_TRUE_FLAGS = ["public_read_only"]

FORBIDDEN_CODE_TOKENS = [
    "create" + "_order",
    "place" + "_order",
    "submit" + "_order",
    "/api/v3/account",
    "/api/v3/order",
    "api_secret",
    "secret_key",
    "paper_live_enabled = True",
    "trading_enabled = True",
]


def validate_safety_flags(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in EXPECTED_TRUE_FLAGS:
        if payload.get(field) is not True:
            errors.append(f"{field} must be true")
    for field in EXPECTED_FALSE_FLAGS:
        if payload.get(field) is not False:
            errors.append(f"{field} must be false")
    return errors


def scan_new_modules_for_forbidden_terms(root: Path) -> list[str]:
    errors: list[str] = []
    paths = [
        root / "src/galapagos/data/public_market",
        root / "scripts/run_public_market_ingestion_preview_v2_3.py",
    ]
    for base in paths:
        candidates = [base] if base.is_file() else list(base.rglob("*.py"))
        for path in candidates:
            if "__pycache__" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            for token in FORBIDDEN_CODE_TOKENS:
                if token in text:
                    errors.append(f"forbidden safety token in {path.relative_to(root)}: {token}")
    return errors
