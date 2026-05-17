from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .feature_preview_reader import sha256
from .label_preview_builder import ALLOWED_ROOT, EXPECTED_FILES
from .label_semantic_guard import scan_label_payloads


class LabelPreviewPhysicalAuditor:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.output_root = root / ALLOWED_ROOT

    def audit(self) -> dict[str, Any]:
        existing = sorted(path.name for path in self.output_root.glob("*") if path.is_file()) if self.output_root.exists() else []
        missing = sorted(set(EXPECTED_FILES) - set(existing))
        unexpected = sorted(set(existing) - set(EXPECTED_FILES))
        payloads: dict[str, Any] = {}
        json_valid = True
        for name in EXPECTED_FILES:
            path = self.output_root / name
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
        for name in EXPECTED_FILES:
            if name == "label_preview_manifest.json":
                continue
            path = self.output_root / name
            if not path.exists() or declared.get(name) != sha256(path):
                checksums_verified = False
        rows_payload = payloads.get("label_preview_rows.json", {})
        rows = rows_payload.get("rows", []) if isinstance(rows_payload, dict) and isinstance(rows_payload.get("rows"), list) else []
        schema = payloads.get("label_preview_schema.json", {})
        fields = schema.get("fields", []) if isinstance(schema, dict) and isinstance(schema.get("fields"), list) else []
        total_bytes = sum((self.output_root / name).stat().st_size for name in existing)
        semantic = scan_label_payloads(payloads)
        timestamp_audit = _audit_label_timestamps(rows)
        return {
            "label_preview_physical_audit_executed": True,
            "created_files_count": len(existing),
            "total_new_data_files_created": len(existing),
            "expected_files_count": len(EXPECTED_FILES),
            "missing_expected_files_count": len(missing),
            "unexpected_files_count": len(unexpected),
            "missing_expected_files": missing,
            "unexpected_files": unexpected,
            "label_files_json_valid": json_valid,
            "label_preview_checksums_verified": checksums_verified,
            "total_data_bytes_written": total_bytes,
            "label_preview_rows_count": len(rows),
            "theoretical_labels_count": len(fields),
            "created_file_paths": [str(ALLOWED_ROOT / name) for name in EXPECTED_FILES],
            "parquet_created": False,
            "csv_created": False,
            "sqlite_created": False,
            "jsonl_created": False,
            "db_created": False,
            **timestamp_audit,
            **semantic,
        }


def _parse_iso8601_z(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        text = value.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except Exception:
        return None


def _audit_label_timestamps(rows: list[Any]) -> dict[str, Any]:
    violations: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            violations.append({
                "row_index": index,
                "field_pair": "row",
                "left_value": None,
                "right_value": None,
                "rule": "row must be an object",
            })
            continue
        decision_raw = row.get("source_decision_ts")
        label_raw = row.get("label_available_ts")
        horizon = row.get("horizon_seconds")
        decision_dt = _parse_iso8601_z(decision_raw)
        label_dt = _parse_iso8601_z(label_raw)
        if decision_raw is None:
            violations.append({"row_index": index, "field_pair": "source_decision_ts", "left_value": None, "right_value": label_raw, "rule": "source_decision_ts exists"})
        if label_raw is None:
            violations.append({"row_index": index, "field_pair": "label_available_ts", "left_value": decision_raw, "right_value": None, "rule": "label_available_ts exists"})
        if horizon is None:
            violations.append({"row_index": index, "field_pair": "horizon_seconds", "left_value": horizon, "right_value": None, "rule": "horizon_seconds exists"})
        if decision_raw is not None and decision_dt is None:
            violations.append({"row_index": index, "field_pair": "source_decision_ts", "left_value": decision_raw, "right_value": None, "rule": "source_decision_ts ISO-8601 valid"})
        if label_raw is not None and label_dt is None:
            violations.append({"row_index": index, "field_pair": "label_available_ts", "left_value": label_raw, "right_value": None, "rule": "label_available_ts ISO-8601 valid"})
        if not isinstance(horizon, int) or horizon <= 0:
            violations.append({"row_index": index, "field_pair": "horizon_seconds", "left_value": horizon, "right_value": None, "rule": "horizon_seconds positive integer"})
        if decision_dt is None or label_dt is None or not isinstance(horizon, int) or horizon <= 0:
            continue
        if label_dt <= decision_dt:
            violations.append({
                "row_index": index,
                "field_pair": "label_available_ts/source_decision_ts",
                "left_value": label_raw,
                "right_value": decision_raw,
                "rule": "label_available_ts > source_decision_ts",
            })
        horizon_dt = decision_dt + timedelta(seconds=horizon)
        if label_dt < horizon_dt:
            violations.append({
                "row_index": index,
                "field_pair": "label_available_ts/source_decision_ts+horizon_seconds",
                "left_value": label_raw,
                "right_value": horizon_dt.isoformat().replace("+00:00", "Z"),
                "rule": "label_available_ts >= source_decision_ts + horizon_seconds",
            })
    return {
        "physical_label_timestamp_audit_executed": True,
        "label_available_after_horizon": not violations,
        "labels_available_at_decision_ts": any(
            item["rule"] == "label_available_ts > source_decision_ts" for item in violations
        ),
        "label_timestamp_order_valid": not violations,
        "label_timestamp_violations_detected": bool(violations),
        "label_timestamp_violations_count": len(violations),
        "label_timestamp_violations": violations,
    }
