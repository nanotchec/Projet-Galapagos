from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .feature_semantic_guard import scan_feature_payloads

ALLOWED_ROOT = Path("data/research/feature_preview/v1_95")
EXPECTED_FILES = [
    "feature_preview_manifest.json",
    "feature_preview_schema.json",
    "feature_preview_rows.json",
    "feature_preview_quality_audit.json",
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


class FeaturePreviewBuilder:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.output_root = root / ALLOWED_ROOT

    def build_payloads(self, schema: dict[str, Any], dryrun: dict[str, Any]) -> dict[str, dict[str, Any]]:
        features = schema.get("theoretical_features", [])[:20]
        rows = dryrun.get("preview_rows", [])[:10]
        feature_names = [feature["feature_name"] for feature in features]
        schema_payload = {
            "version": "V1.95",
            "feature_count": len(feature_names),
            "features": features,
            "timestamp_policy": {
                "event_ts_required": True,
                "available_ts_required": True,
                "decision_ts_required": True,
                "available_ts_lte_decision_ts": True,
            },
        }
        rows_payload = {
            "version": "V1.95",
            "preview_rows_count": len(rows),
            "rows": rows,
        }
        quality_payload = {
            "version": "V1.95",
            "preview_rows_count": len(rows),
            "theoretical_features_count": len(feature_names),
            "json_only": True,
            "supervised_outputs_absent": True,
            "model_outputs_absent": True,
            "training_absent": True,
            "no_trading": True,
            "available_ts_lte_decision_ts_checked": True,
        }
        return {
            "feature_preview_schema.json": schema_payload,
            "feature_preview_rows.json": rows_payload,
            "feature_preview_quality_audit.json": quality_payload,
        }

    def materialize(self, schema: dict[str, Any], dryrun: dict[str, Any]) -> dict[str, Any]:
        payloads = self.build_payloads(schema, dryrun)
        semantic = scan_feature_payloads(payloads)
        if semantic["forbidden_feature_terms_detected"]:
            raise ValueError(f"Forbidden feature term detected: {semantic['forbidden_feature_term_occurrences']}")
        self.output_root.mkdir(parents=True, exist_ok=True)
        for existing in self.output_root.glob("*"):
            if existing.is_file() and existing.name not in EXPECTED_FILES:
                raise ValueError(f"Unexpected file in output root: {existing}")
        for name, payload in payloads.items():
            _write_json(self.output_root / name, payload)
        checksums = {name: _sha256(self.output_root / name) for name in payloads}
        manifest = {
            "version": "V1.95",
            "created_files": [str(ALLOWED_ROOT / name) for name in EXPECTED_FILES],
            "feature_preview_file_checksums": checksums,
            "allowed_data_write_root": str(ALLOWED_ROOT) + "/",
            "total_new_data_files_created": 4,
            "json_only": True,
            "source_versions": ["V1.92.1", "V1.94"],
        }
        _write_json(self.output_root / "feature_preview_manifest.json", manifest)
        return {"created_file_paths": [str(ALLOWED_ROOT / name) for name in EXPECTED_FILES]}
