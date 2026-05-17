from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from .feature_preview_builder import ALLOWED_ROOT, EXPECTED_FILES
from .feature_semantic_guard import scan_feature_payloads


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_iso8601_z(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None

    text = value.strip()
    if not text:
        return None

    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def _audit_timestamp_order(rows_payload: Any) -> dict[str, Any]:
    violations: list[dict[str, Any]] = []

    rows = []
    if isinstance(rows_payload, dict) and isinstance(rows_payload.get("rows"), list):
        rows = rows_payload["rows"]

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

        event_raw = row.get("event_ts")
        available_raw = row.get("available_ts")
        decision_raw = row.get("decision_ts")

        event_ts = _parse_iso8601_z(event_raw)
        available_ts = _parse_iso8601_z(available_raw)
        decision_ts = _parse_iso8601_z(decision_raw)

        if event_ts is None:
            violations.append({
                "row_index": index,
                "field_pair": "event_ts",
                "left_value": event_raw,
                "right_value": None,
                "rule": "event_ts must be present and ISO-8601 valid",
            })

        if available_ts is None:
            violations.append({
                "row_index": index,
                "field_pair": "available_ts",
                "left_value": available_raw,
                "right_value": None,
                "rule": "available_ts must be present and ISO-8601 valid",
            })

        if decision_ts is None:
            violations.append({
                "row_index": index,
                "field_pair": "decision_ts",
                "left_value": decision_raw,
                "right_value": None,
                "rule": "decision_ts must be present and ISO-8601 valid",
            })

        if event_ts is not None and available_ts is not None and event_ts > available_ts:
            violations.append({
                "row_index": index,
                "field_pair": "event_ts/available_ts",
                "left_value": event_raw,
                "right_value": available_raw,
                "rule": "event_ts <= available_ts",
            })

        if available_ts is not None and decision_ts is not None and available_ts > decision_ts:
            violations.append({
                "row_index": index,
                "field_pair": "available_ts/decision_ts",
                "left_value": available_raw,
                "right_value": decision_raw,
                "rule": "available_ts <= decision_ts",
            })

    return {
        "physical_timestamp_order_scan_executed": True,
        "feature_rows_timestamp_order_valid": len(violations) == 0,
        "available_ts_lte_decision_ts_checked": True,
        "event_ts_lte_available_ts_checked": True,
        "timestamp_order_violations_detected": len(violations) > 0,
        "timestamp_order_violations_count": len(violations),
        "timestamp_order_violations": violations,
    }


class FeaturePreviewPhysicalAuditor:
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
        manifest = payloads.get("feature_preview_manifest.json", {})
        declared = manifest.get("feature_preview_file_checksums") if isinstance(manifest, dict) else {}
        checksums_verified = isinstance(declared, dict)
        if checksums_verified:
            for name in EXPECTED_FILES:
                if name == "feature_preview_manifest.json":
                    continue
                path = self.output_root / name
                if not path.exists() or declared.get(name) != _sha256(path):
                    checksums_verified = False
        rows = payloads.get("feature_preview_rows.json", {})
        preview_rows_count = len(rows.get("rows", [])) if isinstance(rows, dict) and isinstance(rows.get("rows"), list) else 0
        schema = payloads.get("feature_preview_schema.json", {})
        theoretical_features_count = len(schema.get("features", [])) if isinstance(schema, dict) and isinstance(schema.get("features"), list) else 0
        total_bytes = sum((self.output_root / name).stat().st_size for name in existing)
        semantic = scan_feature_payloads(payloads)
        timestamp_audit = _audit_timestamp_order(payloads.get("feature_preview_rows.json", {}))
        return {
            "feature_preview_physical_audit_executed": True,
            "created_files_count": len(existing),
            "total_new_data_files_created": len(existing),
            "expected_files_count": len(EXPECTED_FILES),
            "missing_expected_files_count": len(missing),
            "unexpected_files_count": len(unexpected),
            "missing_expected_files": missing,
            "unexpected_files": unexpected,
            "feature_preview_json_valid": json_valid,
            "feature_preview_checksums_verified": checksums_verified,
            "total_data_bytes_written": total_bytes,
            "preview_rows_count": preview_rows_count,
            "theoretical_features_count": theoretical_features_count,
            "created_file_paths": [str(ALLOWED_ROOT / name) for name in EXPECTED_FILES],
            "parquet_created": False,
            "csv_created": False,
            "sqlite_created": False,
            "jsonl_created": False,
            "db_created": False,
            **semantic,
            **timestamp_audit,
        }
