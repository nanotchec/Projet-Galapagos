from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .common import parse_utc, sha256

FEATURE_ROOT = Path("data/research/feature_preview/v1_95")
FEATURE_FILES = [
    "feature_preview_manifest.json",
    "feature_preview_schema.json",
    "feature_preview_rows.json",
    "feature_preview_quality_audit.json",
]


class FeaturePreviewReader:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.feature_root = root / FEATURE_ROOT

    def read_payloads(self) -> dict[str, Any]:
        return {name: json.loads((self.feature_root / name).read_text(encoding="utf-8")) for name in FEATURE_FILES}

    def audit(self) -> dict[str, Any]:
        payloads = self.read_payloads()
        manifest = payloads["feature_preview_manifest.json"]
        declared = manifest.get("feature_preview_file_checksums", {})
        checksums_verified = isinstance(declared, dict)
        for name in FEATURE_FILES:
            if name == "feature_preview_manifest.json":
                continue
            if declared.get(name) != sha256(self.feature_root / name):
                checksums_verified = False
        rows = payloads["feature_preview_rows.json"].get("rows", [])
        violations: list[dict[str, object]] = []
        for index, row in enumerate(rows):
            event_ts = parse_utc(row.get("event_ts")) if isinstance(row, dict) else None
            available_ts = parse_utc(row.get("available_ts")) if isinstance(row, dict) else None
            decision_ts = parse_utc(row.get("decision_ts")) if isinstance(row, dict) else None
            if event_ts is None or available_ts is None or decision_ts is None:
                violations.append({"row_index": index, "rule": "valid feature timestamps"})
            elif event_ts > available_ts or available_ts > decision_ts:
                violations.append({"row_index": index, "rule": "event_ts <= available_ts <= decision_ts"})
        return {
            "feature_preview_checksums_verified": checksums_verified,
            "feature_rows_timestamp_order_valid": not violations,
            "feature_timestamp_violations": violations,
            "existing_feature_preview_files_modified": False,
        }
