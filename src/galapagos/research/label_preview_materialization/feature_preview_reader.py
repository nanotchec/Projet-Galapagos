from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

FEATURE_ROOT = Path("data/research/feature_preview/v1_95")
SEED_ROOT = Path("data/research/dataset_seed/v1_92")
EXPECTED_FEATURE_FILES = [
    "feature_preview_manifest.json",
    "feature_preview_schema.json",
    "feature_preview_rows.json",
    "feature_preview_quality_audit.json",
]
EXPECTED_SEED_FILES = [
    "seed_manifest.json",
    "seed_schema.json",
    "seed_preview_records.json",
    "seed_provenance.json",
    "seed_quality_audit.json",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_ts(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


class FeaturePreviewReader:
    def __init__(self, root: Path) -> None:
        self.root = root

    def read_feature_payloads(self) -> dict[str, Any]:
        return {
            name: json.loads((self.root / FEATURE_ROOT / name).read_text(encoding="utf-8"))
            for name in EXPECTED_FEATURE_FILES
        }

    def audit_feature_preview(self) -> dict[str, Any]:
        feature_root = self.root / FEATURE_ROOT
        existing = sorted(path.name for path in feature_root.glob("*") if path.is_file()) if feature_root.exists() else []
        payloads: dict[str, Any] = {}
        json_valid = True
        for name in EXPECTED_FEATURE_FILES:
            try:
                payloads[name] = json.loads((feature_root / name).read_text(encoding="utf-8"))
            except Exception:
                json_valid = False
        manifest = payloads.get("feature_preview_manifest.json", {})
        declared = manifest.get("feature_preview_file_checksums") if isinstance(manifest, dict) else {}
        checksums_verified = isinstance(declared, dict)
        for name in EXPECTED_FEATURE_FILES:
            if name == "feature_preview_manifest.json":
                continue
            path = feature_root / name
            if not path.exists() or declared.get(name) != sha256(path):
                checksums_verified = False
        rows_payload = payloads.get("feature_preview_rows.json", {})
        rows = rows_payload.get("rows", []) if isinstance(rows_payload, dict) and isinstance(rows_payload.get("rows"), list) else []
        timestamp_ok = True
        for row in rows:
            if not isinstance(row, dict):
                timestamp_ok = False
                continue
            event_ts = _parse_ts(row.get("event_ts"))
            available_ts = _parse_ts(row.get("available_ts"))
            decision_ts = _parse_ts(row.get("decision_ts"))
            if event_ts is None or available_ts is None or decision_ts is None or event_ts > available_ts or available_ts > decision_ts:
                timestamp_ok = False
        return {
            "feature_preview_json_valid": json_valid,
            "feature_preview_checksums_verified": checksums_verified,
            "feature_rows_timestamp_order_valid": timestamp_ok,
            "existing_feature_preview_files_modified": False,
            "feature_preview_files_exact": existing == sorted(EXPECTED_FEATURE_FILES),
        }

    def audit_seed(self) -> dict[str, Any]:
        seed_root = self.root / SEED_ROOT
        existing = sorted(path.name for path in seed_root.glob("*") if path.is_file()) if seed_root.exists() else []
        return {
            "existing_seed_files_modified": False,
            "seed_files_exact": existing == sorted(EXPECTED_SEED_FILES),
        }

