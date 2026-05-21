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

FORBIDDEN_POSITIVE_CLAIMS = [
    "strategy validated",
    "stratégie validée",
    "strategie validee",
    "signal validated",
    "signal validé",
    "signal valide",
    "trading enabled",
    "trading activé",
    "trading active",
    "paper live enabled",
    "paper live activé",
    "paper live active",
    "orders enabled",
    "ordre activé",
    "ordre active",
    "real trading",
    "trading réel activé",
    "trading reel active",
    "ml validated",
    "modèle ml validé",
    "modele ml valide",
    "backtest validated",
    "backtest validé",
    "backtest valide",
    "execution enabled",
    "live enabled",
    "production ready",
    "ordre réel activé",
    "ordre reel active",
    "strategy_validated",
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


def validate_exact_keys(payload: Any, expected_keys: set[str], label: str) -> list[str]:
    if not isinstance(payload, dict):
        return [f"{label} must be an object"]
    actual_keys = set(payload)
    errors: list[str] = []
    unexpected = sorted(actual_keys - expected_keys)
    missing = sorted(expected_keys - actual_keys)
    if unexpected:
        errors.append(f"{label} unexpected keys: {unexpected}")
    if missing:
        errors.append(f"{label} missing keys: {missing}")
    return errors


def scan_payload_for_forbidden_claims(payload: Any, label: str) -> list[str]:
    errors: list[str] = []

    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}" if path else str(key)
                key_text = str(key).casefold()
                for term in FORBIDDEN_POSITIVE_CLAIMS:
                    if term.casefold() in key_text:
                        errors.append(f"{label} contains forbidden claim at {child_path}: {term}")
                walk(child, child_path)
            return
        if isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")
            return
        if isinstance(value, str):
            text = value.casefold()
            for term in FORBIDDEN_POSITIVE_CLAIMS:
                if term.casefold() in text:
                    errors.append(f"{label} contains forbidden claim at {path}: {term}")

    walk(payload, "")
    return errors


def validate_markdown_forbidden_claims(text: str, label: str) -> list[str]:
    lowered = text.casefold()
    return [
        f"{label} contains forbidden claim: {term}"
        for term in FORBIDDEN_POSITIVE_CLAIMS
        if term.casefold() in lowered
    ]


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
