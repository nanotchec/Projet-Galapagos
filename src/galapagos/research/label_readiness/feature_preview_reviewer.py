from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from galapagos.research.feature_preview_materialization.feature_semantic_guard import scan_feature_payloads

from .anti_leakage_label_guard import parse_utc

FEATURE_PREVIEW_ROOT = Path("data/research/feature_preview/v1_95")
EXPECTED_FEATURE_FILES = [
    "feature_preview_manifest.json",
    "feature_preview_schema.json",
    "feature_preview_rows.json",
    "feature_preview_quality_audit.json",
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class FeaturePreviewReviewer:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.feature_root = root / FEATURE_PREVIEW_ROOT

    def read_payloads(self) -> dict[str, Any]:
        return {
            name: json.loads((self.feature_root / name).read_text(encoding="utf-8"))
            for name in EXPECTED_FEATURE_FILES
        }

    def audit(self) -> dict[str, Any]:
        existing = sorted(path.name for path in self.feature_root.glob("*") if path.is_file()) if self.feature_root.exists() else []
        missing = sorted(set(EXPECTED_FEATURE_FILES) - set(existing))
        unexpected = sorted(set(existing) - set(EXPECTED_FEATURE_FILES))
        payloads: dict[str, Any] = {}
        json_valid = True
        for name in EXPECTED_FEATURE_FILES:
            path = self.feature_root / name
            if not path.exists():
                json_valid = False
                continue
            try:
                payloads[name] = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                json_valid = False

        manifest = payloads.get("feature_preview_manifest.json", {})
        declared = manifest.get("feature_preview_file_checksums") if isinstance(manifest, dict) else {}
        checksums_verified = isinstance(declared, dict)
        if checksums_verified:
            for name in EXPECTED_FEATURE_FILES:
                if name == "feature_preview_manifest.json":
                    continue
                path = self.feature_root / name
                if not path.exists() or declared.get(name) != _sha256(path):
                    checksums_verified = False

        rows_payload = payloads.get("feature_preview_rows.json", {})
        rows = rows_payload.get("rows", []) if isinstance(rows_payload, dict) and isinstance(rows_payload.get("rows"), list) else []
        violations = []
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                violations.append({"row_index": index, "rule": "row must be an object"})
                continue
            event_ts = parse_utc(row.get("event_ts"))
            available_ts = parse_utc(row.get("available_ts"))
            decision_ts = parse_utc(row.get("decision_ts"))
            if event_ts is None or available_ts is None or decision_ts is None:
                violations.append({"row_index": index, "rule": "timestamps must be valid ISO-8601"})
                continue
            if event_ts > available_ts:
                violations.append({"row_index": index, "rule": "event_ts <= available_ts"})
            if available_ts > decision_ts:
                violations.append({"row_index": index, "rule": "available_ts <= decision_ts"})

        schema_payload = payloads.get("feature_preview_schema.json", {})
        features = schema_payload.get("features", []) if isinstance(schema_payload, dict) and isinstance(schema_payload.get("features"), list) else []
        semantic = scan_feature_payloads(payloads)
        return {
            "feature_preview_review_physical_audit_executed": True,
            "reviewed_feature_preview_root": str(FEATURE_PREVIEW_ROOT) + "/",
            "reviewed_feature_preview_files_count": len(existing),
            "expected_feature_preview_files_count": len(EXPECTED_FEATURE_FILES),
            "unexpected_feature_preview_files_count": len(unexpected),
            "missing_feature_preview_files_count": len(missing),
            "unexpected_feature_preview_files": unexpected,
            "missing_feature_preview_files": missing,
            "feature_preview_checksums_verified": checksums_verified,
            "feature_preview_json_valid": json_valid,
            "preview_rows_count": len(rows),
            "theoretical_features_count": len(features),
            "physical_timestamp_order_scan_executed": True,
            "feature_rows_timestamp_order_valid": not violations,
            "available_ts_lte_decision_ts_checked": True,
            "event_ts_lte_available_ts_checked": True,
            "timestamp_order_violations_detected": bool(violations),
            "timestamp_order_violations_count": len(violations),
            "timestamp_order_violations": violations,
            "existing_feature_preview_files_modified": False,
            **semantic,
        }

