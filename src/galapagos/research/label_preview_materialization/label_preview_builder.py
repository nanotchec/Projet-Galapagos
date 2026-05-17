from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .feature_preview_reader import sha256

ALLOWED_ROOT = Path("data/research/label_preview/v1_97")
EXPECTED_FILES = [
    "label_preview_manifest.json",
    "label_preview_schema.json",
    "label_preview_rows.json",
    "label_preview_quality_audit.json",
]


def _parse_iso8601_z(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _format_iso8601_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class LabelPreviewBuilder:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.output_root = root / ALLOWED_ROOT

    def build_payloads(self, feature_payloads: dict[str, Any]) -> dict[str, Any]:
        source_rows = feature_payloads.get("feature_preview_rows.json", {}).get("rows", [])
        rows = []
        for index, row in enumerate(source_rows[:3]):
            decision_raw = row.get("decision_ts") if isinstance(row, dict) else None
            horizon_seconds = 300
            try:
                decision_dt = _parse_iso8601_z(decision_raw)
                label_available_ts = _format_iso8601_z(decision_dt + timedelta(seconds=horizon_seconds))
            except Exception:
                label_available_ts = None
            rows.append({
                "label_preview_id": f"label_preview_{index}",
                "source_row_ref": f"feature_preview_row_{index}",
                "source_decision_ts": decision_raw,
                "horizon_seconds": horizon_seconds,
                "label_available_ts": label_available_ts,
                "label_policy_name": "research_preview_after_horizon_only",
                "label_preview_kind": "direction_placeholder",
                "label_value_placeholder": None,
                "separated_from_features": True,
                "research_only": True,
            })
        schema = {
            "version": "V1.97",
            "theoretical_labels_count": 5,
            "fields": [
                {"name": "horizon_seconds", "dtype": "integer"},
                {"name": "label_available_ts", "dtype": "timestamp"},
                {"name": "label_policy_name", "dtype": "string"},
                {"name": "label_preview_kind", "dtype": "string"},
                {"name": "label_value_placeholder", "dtype": "nullable"},
            ],
            "labels_separated_from_features": True,
        }
        rows_payload = {
            "version": "V1.97",
            "label_preview_rows_count": len(rows),
            "rows": rows,
        }
        quality = {
            "version": "V1.97",
            "labels_separated_from_features": True,
            "feature_label_join_created": False,
            "combined_dataset_created": False,
            "labels_available_at_decision_ts": False,
            "label_available_after_horizon": True,
            "label_not_available_at_decision_ts_policy_applied": True,
            "supervised_learning_ready": False,
            "label_preview_for_research_only": True,
            "no_ml": True,
            "no_network": True,
            "no_trading": True,
        }
        return {
            "label_preview_schema.json": schema,
            "label_preview_rows.json": rows_payload,
            "label_preview_quality_audit.json": quality,
        }

    def write(self, feature_payloads: dict[str, Any]) -> dict[str, Any]:
        self.output_root.mkdir(parents=True, exist_ok=True)
        payloads = self.build_payloads(feature_payloads)
        for name, payload in payloads.items():
            (self.output_root / name).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        manifest = {
            "version": "V1.97",
            "created_files": [str(ALLOWED_ROOT / name) for name in EXPECTED_FILES],
            "label_preview_file_checksums": {
                name: sha256(self.output_root / name)
                for name in EXPECTED_FILES
                if name != "label_preview_manifest.json"
            },
            "allowed_data_write_root": str(ALLOWED_ROOT) + "/",
            "total_new_data_files_created": 4,
            "json_only": True,
            "source_versions": ["V1.95.1", "V1.96.1"],
        }
        (self.output_root / "label_preview_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        return {"created_file_paths": [str(ALLOWED_ROOT / name) for name in EXPECTED_FILES]}
