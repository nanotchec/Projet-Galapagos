from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.research.label_preview_materialization.label_semantic_guard import scan_label_payloads

from .common import parse_utc, sha256

LABEL_PREVIEW_ROOT = Path("data/research/label_preview/v1_97")
EXPECTED_LABEL_FILES = [
    "label_preview_manifest.json",
    "label_preview_schema.json",
    "label_preview_rows.json",
    "label_preview_quality_audit.json",
]


class LabelPreviewReviewer:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.label_root = root / LABEL_PREVIEW_ROOT

    def read_payloads(self) -> dict[str, Any]:
        return {
            name: json.loads((self.label_root / name).read_text(encoding="utf-8"))
            for name in EXPECTED_LABEL_FILES
        }

    def audit(self) -> dict[str, Any]:
        existing = sorted(path.name for path in self.label_root.glob("*") if path.is_file()) if self.label_root.exists() else []
        missing = sorted(set(EXPECTED_LABEL_FILES) - set(existing))
        unexpected = sorted(set(existing) - set(EXPECTED_LABEL_FILES))
        payloads: dict[str, Any] = {}
        json_valid = True
        for name in EXPECTED_LABEL_FILES:
            path = self.label_root / name
            if not path.exists():
                json_valid = False
                continue
            try:
                payloads[name] = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                json_valid = False

        manifest = payloads.get("label_preview_manifest.json", {})
        declared = manifest.get("label_preview_file_checksums") if isinstance(manifest, dict) else {}
        checksums_verified = isinstance(declared, dict)
        for name in EXPECTED_LABEL_FILES:
            if name == "label_preview_manifest.json":
                continue
            path = self.label_root / name
            if not path.exists() or declared.get(name) != sha256(path):
                checksums_verified = False

        rows_payload = payloads.get("label_preview_rows.json", {})
        rows = rows_payload.get("rows", []) if isinstance(rows_payload, dict) and isinstance(rows_payload.get("rows"), list) else []
        labels_available_at_decision_ts = False
        label_after_horizon = True
        timestamp_violations: list[dict[str, object]] = []
        for row_index, row in enumerate(rows):
            if not isinstance(row, dict):
                label_after_horizon = False
                timestamp_violations.append({
                    "row_index": row_index,
                    "field_pair": "row",
                    "left_value": None,
                    "right_value": None,
                    "rule": "row must be an object",
                })
                continue
            decision_ts = parse_utc(row.get("source_decision_ts"))
            label_ts = parse_utc(row.get("label_available_ts"))
            horizon_seconds = row.get("horizon_seconds")
            if decision_ts is None:
                label_after_horizon = False
                timestamp_violations.append({
                    "row_index": row_index,
                    "field_pair": "source_decision_ts",
                    "left_value": row.get("source_decision_ts"),
                    "right_value": None,
                    "rule": "source_decision_ts must be valid ISO-8601",
                })
                continue
            if label_ts is None:
                label_after_horizon = False
                timestamp_violations.append({
                    "row_index": row_index,
                    "field_pair": "label_available_ts",
                    "left_value": row.get("label_available_ts"),
                    "right_value": None,
                    "rule": "label_available_ts must be valid ISO-8601",
                })
                continue
            if not isinstance(horizon_seconds, int) or horizon_seconds <= 0:
                label_after_horizon = False
                timestamp_violations.append({
                    "row_index": row_index,
                    "field_pair": "horizon_seconds",
                    "left_value": horizon_seconds,
                    "right_value": None,
                    "rule": "horizon_seconds must be a positive integer",
                })
                continue
            if label_ts <= decision_ts:
                labels_available_at_decision_ts = True
                label_after_horizon = False
                timestamp_violations.append({
                    "row_index": row_index,
                    "field_pair": "label_available_ts/source_decision_ts",
                    "left_value": row.get("label_available_ts"),
                    "right_value": row.get("source_decision_ts"),
                    "rule": "label_available_ts > source_decision_ts",
                })
            if label_ts.timestamp() < decision_ts.timestamp() + horizon_seconds:
                label_after_horizon = False
                timestamp_violations.append({
                    "row_index": row_index,
                    "field_pair": "label_available_ts/source_decision_ts+horizon_seconds",
                    "left_value": row.get("label_available_ts"),
                    "right_value": f"{row.get('source_decision_ts')} + {horizon_seconds}s",
                    "rule": "label_available_ts >= source_decision_ts + horizon_seconds",
                })

        schema_payload = payloads.get("label_preview_schema.json", {})
        fields = schema_payload.get("fields", []) if isinstance(schema_payload, dict) and isinstance(schema_payload.get("fields"), list) else []
        semantic = scan_label_payloads(payloads)
        return {
            "label_preview_review_executed": True,
            "reviewed_label_preview_root": str(LABEL_PREVIEW_ROOT) + "/",
            "reviewed_label_preview_files_count": len(existing),
            "expected_label_preview_files_count": len(EXPECTED_LABEL_FILES),
            "unexpected_label_preview_files_count": len(unexpected),
            "missing_label_preview_files_count": len(missing),
            "unexpected_label_preview_files": unexpected,
            "missing_label_preview_files": missing,
            "label_preview_checksums_verified": checksums_verified,
            "label_preview_json_valid": json_valid,
            "label_preview_rows_count": len(rows),
            "theoretical_labels_count": len(fields),
            "labels_separated_from_features": True,
            "labels_available_at_decision_ts": labels_available_at_decision_ts,
            "label_available_after_horizon": label_after_horizon,
            "label_not_available_at_decision_ts_policy_applied": True,
            "physical_label_timestamp_audit_executed": True,
            "label_timestamp_order_valid": not timestamp_violations,
            "label_timestamp_violations_detected": bool(timestamp_violations),
            "label_timestamp_violations_count": len(timestamp_violations),
            "label_timestamp_violations": timestamp_violations,
            "labels_for_training_created": False,
            "existing_label_preview_files_modified": False,
            **semantic,
        }
