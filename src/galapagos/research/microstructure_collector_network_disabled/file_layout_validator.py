from __future__ import annotations
from pathlib import Path


class FileLayoutValidator:
    """Checks for expected storage structure."""

    @staticmethod
    def get_expected_path(source: str, symbol: str, timeframe: str) -> str:
        """Returns the expected path pattern for storage."""
        return f"data/silver/intrabar/{source}/{symbol}/{timeframe}/"

    @staticmethod
    def check_local_existence(path: str) -> bool:
        """Checks if a directory exists locally (safe check)."""
        # In V1.54, we don't expect new data, so this check is just for the structure
        return Path(path).exists()
