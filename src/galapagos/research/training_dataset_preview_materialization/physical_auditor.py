from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .common import sha256
from .join_builder import OUTPUT_FILES, OUTPUT_ROOT
from .semantic_guard import scan_training_preview_payloads


class TrainingDatasetPreviewPhysicalAuditor:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.output_root = root / OUTPUT_ROOT

    def read_payloads(self) -> dict[str, Any]:
        return {name: json.loads((self.output_root / name).read_text(encoding="utf-8")) for name in OUTPUT_FILES}

    def audit(self) -> dict[str, Any]:
        existing = sorted(path.name for path in self.output_root.glob("*") if path.is_file()) if self.output_root.exists() else []
        missing = sorted(set(OUTPUT_FILES) - set(existing))
        unexpected = sorted(set(existing) - set(OUTPUT_FILES))
        payloads: dict[str, Any] = {}
        json_valid = True
        for name in OUTPUT_FILES:
            path = self.output_root / name
            if not path.exists():
                json_valid = False
                continue
            try:
                payloads[name] = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                json_valid = False
        manifest = payloads.get("training_dataset_preview_manifest.json", {})
        declared = manifest.get("training_dataset_preview_file_checksums") if isinstance(manifest, dict) else {}
        checksums_verified = isinstance(declared, dict)
        for name in OUTPUT_FILES:
            if name == "training_dataset_preview_manifest.json":
                continue
            path = self.output_root / name
            if not path.exists() or declared.get(name) != sha256(path):
                checksums_verified = False
        rows_payload = payloads.get("training_dataset_preview_rows.json", {})
        rows = rows_payload.get("rows", []) if isinstance(rows_payload, dict) and isinstance(rows_payload.get("rows"), list) else []
        split = payloads.get("training_dataset_preview_split_policy.json", {})
        quality = payloads.get("training_dataset_preview_quality_audit.json", {})
        semantic = scan_training_preview_payloads(payloads)
        forbidden_extensions = {".parquet", ".csv", ".sqlite", ".jsonl", ".db"}
        forbidden_files = [name for name in existing if Path(name).suffix.lower() in forbidden_extensions]
        total_bytes = sum((self.output_root / name).stat().st_size for name in existing if (self.output_root / name).is_file())
        return {
            "training_dataset_preview_physical_audit_executed": True,
            "expected_training_dataset_preview_files_count": len(OUTPUT_FILES),
            "reviewed_training_dataset_preview_files_count": len(existing),
            "missing_training_dataset_preview_files_count": len(missing),
            "unexpected_training_dataset_preview_files_count": len(unexpected),
            "missing_training_dataset_preview_files": missing,
            "unexpected_training_dataset_preview_files": unexpected,
            "training_dataset_preview_json_valid": json_valid,
            "training_dataset_preview_checksums_verified": checksums_verified,
            "forbidden_files_detected": bool(forbidden_files),
            "forbidden_files": forbidden_files,
            "total_data_bytes_written": total_bytes,
            "training_preview_rows_count": len(rows),
            "joined_feature_label_pairs_count": len(rows),
            "split_policy_created": split.get("split_policy_created") is True,
            "purge_policy_defined": split.get("purge_policy_defined") is True,
            "embargo_policy_defined": split.get("embargo_policy_defined") is True,
            "temporal_split_policy_defined": split.get("temporal_split_policy_defined") is True,
            "no_random_shuffle_policy_defined": split.get("no_random_shuffle_policy_defined") is True,
            "random_shuffle_used": split.get("random_shuffle_used") is True,
            "anti_leakage_join_guard_applied": quality.get("anti_leakage_join_guard_applied") is True,
            "label_availability_policy_applied": quality.get("label_availability_policy_applied") is True,
            "purge_policy_applied": quality.get("purge_policy_applied") is True,
            "embargo_policy_applied": quality.get("embargo_policy_applied") is True,
            "temporal_split_policy_applied": quality.get("temporal_split_policy_applied") is True,
            "no_random_shuffle_policy_applied": quality.get("no_random_shuffle_policy_applied") is True,
            "alignment_leakage_detected": quality.get("alignment_leakage_detected") is True,
            "alignment_lookahead_detected": quality.get("alignment_lookahead_detected") is True,
            "training_dataset_leakage_detected": quality.get("training_dataset_leakage_detected") is True,
            "training_dataset_lookahead_detected": quality.get("training_dataset_lookahead_detected") is True,
            **semantic,
        }
