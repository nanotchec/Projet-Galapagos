from __future__ import annotations
from typing import Dict, Any


class ManifestValidator:
    """Validates theoretical data manifests."""

    @staticmethod
    def validate_schema(manifest: Dict[str, Any]) -> bool:
        """Checks if the manifest contains all required fields."""
        required_fields = [
            "event_ts",
            "available_ts",
            "ingest_ts",
            "source",
            "symbol",
            "timeframe",
            "row_count"
        ]
        return all(field in manifest for field in required_fields)

    @staticmethod
    def validate_causality(manifest: Dict[str, Any]) -> bool:
        """Basic causality check: available_ts must be after event_ts."""
        if not ManifestValidator.validate_schema(manifest):
            return False
        return manifest["available_ts"] >= manifest["event_ts"]
