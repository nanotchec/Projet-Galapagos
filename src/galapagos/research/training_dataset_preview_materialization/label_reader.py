from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .common import parse_utc, sha256

LABEL_ROOT = Path("data/research/label_preview/v1_97")
LABEL_FILES = [
    "label_preview_manifest.json",
    "label_preview_schema.json",
    "label_preview_rows.json",
    "label_preview_quality_audit.json",
]


class LabelPreviewReader:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.label_root = root / LABEL_ROOT

    def read_payloads(self) -> dict[str, Any]:
        return {name: json.loads((self.label_root / name).read_text(encoding="utf-8")) for name in LABEL_FILES}

    def audit(self) -> dict[str, Any]:
        payloads = self.read_payloads()
        manifest = payloads["label_preview_manifest.json"]
        declared = manifest.get("label_preview_file_checksums", {})
        checksums_verified = isinstance(declared, dict)
        for name in LABEL_FILES:
            if name == "label_preview_manifest.json":
                continue
            if declared.get(name) != sha256(self.label_root / name):
                checksums_verified = False
        rows = payloads["label_preview_rows.json"].get("rows", [])
        violations: list[dict[str, object]] = []
        labels_available_at_decision_ts = False
        label_available_after_horizon = True
        for index, row in enumerate(rows):
            decision_ts = parse_utc(row.get("source_decision_ts")) if isinstance(row, dict) else None
            label_ts = parse_utc(row.get("label_available_ts")) if isinstance(row, dict) else None
            horizon = row.get("horizon_seconds") if isinstance(row, dict) else None
            if decision_ts is None or label_ts is None or not isinstance(horizon, int) or horizon <= 0:
                label_available_after_horizon = False
                violations.append({"row_index": index, "rule": "valid label timestamp fields"})
                continue
            if label_ts <= decision_ts:
                labels_available_at_decision_ts = True
                label_available_after_horizon = False
                violations.append({"row_index": index, "rule": "label_available_ts > source_decision_ts"})
            if label_ts.timestamp() < decision_ts.timestamp() + horizon:
                label_available_after_horizon = False
                violations.append({"row_index": index, "rule": "label_available_ts >= source_decision_ts + horizon_seconds"})
        return {
            "label_preview_checksums_verified": checksums_verified,
            "label_timestamp_order_valid": not violations,
            "label_timestamp_violations_detected": bool(violations),
            "label_timestamp_violations_count": len(violations),
            "label_timestamp_violations": violations,
            "labels_available_at_decision_ts": labels_available_at_decision_ts,
            "label_available_after_horizon": label_available_after_horizon,
            "existing_label_preview_files_modified": False,
        }
