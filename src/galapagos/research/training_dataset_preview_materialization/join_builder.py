from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .anti_leakage_join_guard import AntiLeakageJoinGuard
from .common import sha256
from .split_policy_builder import SplitPolicyBuilder

OUTPUT_ROOT = Path("data/research/training_dataset_preview/v1_99")
OUTPUT_FILES = [
    "training_dataset_preview_manifest.json",
    "training_dataset_preview_schema.json",
    "training_dataset_preview_rows.json",
    "training_dataset_preview_split_policy.json",
    "training_dataset_preview_quality_audit.json",
]


class TrainingDatasetPreviewBuilder:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.output_root = root / OUTPUT_ROOT

    def build_payloads(self, feature_payloads: dict[str, Any], label_payloads: dict[str, Any]) -> dict[str, Any]:
        feature_rows = feature_payloads["feature_preview_rows.json"].get("rows", [])[:10]
        label_rows = label_payloads["label_preview_rows.json"].get("rows", [])[:10]
        joined: list[dict[str, Any]] = []
        for index, (feature, label) in enumerate(zip(feature_rows, label_rows)):
            joined.append({
                "preview_row_id": f"training_preview_row_{index}",
                "feature_row_ref": f"feature_preview_row_{index}",
                "label_row_ref": label.get("label_preview_id"),
                "event_ts": feature.get("event_ts"),
                "available_ts": feature.get("available_ts"),
                "decision_ts": feature.get("decision_ts"),
                "label_available_ts": label.get("label_available_ts"),
                "horizon_seconds": label.get("horizon_seconds"),
                "label_available_at_decision_ts": False,
                "research_only": True,
                "usable_for_direct_ml": False,
                "features": {
                    key: value
                    for key, value in feature.items()
                    if key not in {"event_ts", "available_ts", "decision_ts"}
                },
                "label_preview": {
                    "label_policy_name": label.get("label_policy_name"),
                    "label_preview_kind": label.get("label_preview_kind"),
                    "label_value_placeholder": label.get("label_value_placeholder"),
                },
            })
        schema = {
            "version": "V1.99",
            "artifact": "training_dataset_preview",
            "fields": [
                "preview_row_id",
                "feature_row_ref",
                "label_row_ref",
                "event_ts",
                "available_ts",
                "decision_ts",
                "label_available_ts",
                "horizon_seconds",
                "research_only",
                "usable_for_direct_ml",
                "features",
                "label_preview",
            ],
            "max_rows": 10,
            "max_pairs": 10,
        }
        rows = {
            "version": "V1.99",
            "training_preview_rows_count": len(joined),
            "joined_feature_label_pairs_count": len(joined),
            "rows": joined,
        }
        split_policy = SplitPolicyBuilder().build()
        leakage = AntiLeakageJoinGuard().audit(joined)
        quality = {
            "version": "V1.99",
            "json_only": True,
            "created_files_count": 5,
            "row_limit_respected": len(joined) <= 10,
            "pair_limit_respected": len(joined) <= 10,
            "research_only": True,
            "direct_ml_use_allowed": False,
            **leakage,
        }
        return {
            "training_dataset_preview_schema.json": schema,
            "training_dataset_preview_rows.json": rows,
            "training_dataset_preview_split_policy.json": split_policy,
            "training_dataset_preview_quality_audit.json": quality,
        }

    def write(self, payloads: dict[str, Any]) -> dict[str, Any]:
        self.output_root.mkdir(parents=True, exist_ok=True)
        for old in self.output_root.glob("*"):
            if old.is_file() and old.name not in OUTPUT_FILES:
                raise ValueError(f"Unexpected file in V1.99 output root: {old}")
        for name, payload in payloads.items():
            (self.output_root / name).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        checksums = {name: sha256(self.output_root / name) for name in payloads}
        manifest = {
            "version": "V1.99",
            "created_files": [str(OUTPUT_ROOT / name) for name in OUTPUT_FILES],
            "training_dataset_preview_file_checksums": checksums,
            "allowed_data_write_root": str(OUTPUT_ROOT) + "/",
            "total_new_data_files_created": 5,
            "json_only": True,
            "source_versions": ["V1.95.1", "V1.97.2", "V1.98.2"],
        }
        (self.output_root / "training_dataset_preview_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        files = [self.output_root / name for name in OUTPUT_FILES]
        return {
            "created_file_paths": [str(path.relative_to(self.root)) for path in files],
            "total_data_bytes_written": sum(path.stat().st_size for path in files),
        }
