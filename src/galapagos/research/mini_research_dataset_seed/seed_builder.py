from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .anti_leakage_guard import MiniResearchDatasetSeedAntiLeakageGuard
from .physical_auditor import MiniResearchDatasetSeedPhysicalAuditor, sha256_file

ALLOWED_DATA_WRITE_ROOT = Path("data/research/dataset_seed/v1_92")
ALLOWED_FILES = [
    ALLOWED_DATA_WRITE_ROOT / "seed_manifest.json",
    ALLOWED_DATA_WRITE_ROOT / "seed_schema.json",
    ALLOWED_DATA_WRITE_ROOT / "seed_preview_records.json",
    ALLOWED_DATA_WRITE_ROOT / "seed_provenance.json",
    ALLOWED_DATA_WRITE_ROOT / "seed_quality_audit.json",
]
MAX_FILES = 5
MAX_BYTES = 50_000
MAX_PREVIEW_RECORDS = 10
AUTHORIZED_SCOPE = "mini_research_dataset_seed_ultra_bounded_no_network_no_full_dataset_no_ml_no_trading"


class SeedBuildError(ValueError):
    """Raised when V1.92 seed creation would violate the approved scope."""


class MiniResearchDatasetSeedBuilder:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()
        self.allowed_root = self.project_root / ALLOWED_DATA_WRITE_ROOT
        self.allowed_paths = [self.project_root / path for path in ALLOWED_FILES]

    def build(
        self,
        *,
        approval: dict[str, Any],
        design: dict[str, Any],
        anti_leakage_plan: dict[str, Any],
        version: str = "V1.92",
    ) -> dict[str, Any]:
        if not self._approval_is_valid(approval):
            raise SeedBuildError("V1.92 seed requires validated V1.91.4 approval.")
        if not self._design_is_valid(design):
            raise SeedBuildError("V1.92 seed requires bounded V1.91.4 design.")
        if not self._anti_leakage_plan_is_valid(anti_leakage_plan):
            raise SeedBuildError("V1.92 seed requires complete V1.91.4 anti-leakage plan.")

        auditor = MiniResearchDatasetSeedPhysicalAuditor(self.project_root)
        pre = auditor.audit_existing_sources()
        if not (pre["v1_84_hashes_verified"] and pre["v1_87_hashes_verified"] and pre["v1_90_hashes_verified"]):
            raise SeedBuildError("Source hash verification failed before V1.92 write.")

        self.allowed_root.mkdir(parents=True, exist_ok=True)
        payloads = self._build_payloads(source_audit=pre, version=version)
        anti = MiniResearchDatasetSeedAntiLeakageGuard().check_seed_payloads(payloads[1:4])
        if anti["leakage_detected"]:
            raise SeedBuildError(f"Forbidden seed fields detected: {anti['forbidden_fields']}")

        named_payloads = dict(zip([path.name for path in self.allowed_paths], payloads, strict=True))
        for path in self.allowed_paths[1:]:
            self._write_json(path, named_payloads[path.name])

        checksums = {
            path.name: sha256_file(path)
            for path in self.allowed_paths[1:]
        }
        manifest = named_payloads["seed_manifest.json"]
        manifest["seed_file_checksums"] = checksums
        self._write_json(self.allowed_paths[0], manifest)

        post = auditor.audit_seed_outputs(
            pre_v1_84_hashes=pre["v1_84_hashes_observed"],
            pre_v1_87_hashes=pre["v1_87_hashes_observed"],
            pre_v1_90_hashes=pre["v1_90_hashes_observed"],
        )
        if post["created_files_count"] != MAX_FILES or post["total_data_bytes_written"] > MAX_BYTES:
            raise SeedBuildError("V1.92 seed output limits violated.")
        return {**post, **anti}

    def _approval_is_valid(self, approval: dict[str, Any]) -> bool:
        return (
            approval.get("human_approval_granted") is True
            and approval.get("approval_phrase_match") is True
            and approval.get("v1_92_authorized") is True
            and approval.get("authorized_future_scope") == AUTHORIZED_SCOPE
        )

    def _design_is_valid(self, design: dict[str, Any]) -> bool:
        return (
            design.get("dataset_seed_design_created") is True
            and design.get("future_dataset_seed_allowed_root") == f"{ALLOWED_DATA_WRITE_ROOT}/"
            and design.get("future_dataset_seed_max_files") <= MAX_FILES
            and design.get("future_dataset_seed_max_bytes") <= MAX_BYTES
            and design.get("future_dataset_seed_allowed_extensions") == [".json"]
        )

    def _anti_leakage_plan_is_valid(self, plan: dict[str, Any]) -> bool:
        return all(
            plan.get(field) is True
            for field in [
                "anti_leakage_plan_created",
                "available_ts_policy_defined",
                "event_ts_policy_defined",
                "decision_ts_policy_defined",
                "feature_available_ts_lte_decision_ts_rule_defined",
                "no_lookahead_policy_defined",
                "provenance_policy_defined",
                "manifest_checksum_policy_defined",
                "schema_validation_policy_defined",
            ]
        )

    def _build_payloads(self, *, source_audit: dict[str, Any], version: str) -> list[dict[str, Any]]:
        base = {
            "version": version,
            "source_versions": ["V1.84", "V1.87.2", "V1.90.1"],
            "event_ts": "source_artifact_static",
            "available_ts": "source_artifact_static",
            "decision_ts": "v1_92_seed_build_time",
            "anti_leakage_note": "available_ts must be less than or equal to decision_ts",
        }
        schema = {
            **base,
            "artifact": "seed_schema",
            "fields": [
                {"name": "source_version", "type": "string"},
                {"name": "artifact_name", "type": "string"},
                {"name": "artifact_kind", "type": "string"},
                {"name": "event_ts", "type": "string"},
                {"name": "available_ts", "type": "string"},
                {"name": "decision_ts", "type": "string"},
                {"name": "source_checksum_sha256", "type": "string"},
            ],
            "available_ts_policy": "feature_available_ts_lte_decision_ts",
            "no_lookahead_policy": "source artifact metadata only; no prohibited result fields",
        }
        records = [
            {
                "source_version": "V1.84",
                "artifact_name": "manifest.json",
                "artifact_kind": "base_materialization_manifest",
                "event_ts": "source_artifact_static",
                "available_ts": "source_artifact_static",
                "decision_ts": "v1_92_seed_build_time",
                "source_checksum_sha256": source_audit["v1_84_hashes_observed"]["manifest.json"],
            },
            {
                "source_version": "V1.87.2",
                "artifact_name": "extension_manifest.json",
                "artifact_kind": "extension_manifest",
                "event_ts": "source_artifact_static",
                "available_ts": "source_artifact_static",
                "decision_ts": "v1_92_seed_build_time",
                "source_checksum_sha256": source_audit["v1_87_hashes_observed"]["extension_manifest.json"],
            },
            {
                "source_version": "V1.90.1",
                "artifact_name": "consolidated_manifest.json",
                "artifact_kind": "consolidation_manifest",
                "event_ts": "source_artifact_static",
                "available_ts": "source_artifact_static",
                "decision_ts": "v1_92_seed_build_time",
                "source_checksum_sha256": source_audit["v1_90_hashes_observed"]["consolidated_manifest.json"],
            },
        ]
        preview = {
            **base,
            "artifact": "seed_preview_records",
            "preview_records_count": len(records),
            "records": records,
        }
        provenance = {
            **base,
            "artifact": "seed_provenance",
            "references_v1_84": True,
            "references_v1_87": True,
            "references_v1_90": True,
            "source_hashes": {
                "v1_84": source_audit["v1_84_hashes_observed"],
                "v1_87": source_audit["v1_87_hashes_observed"],
                "v1_90": source_audit["v1_90_hashes_observed"],
            },
        }
        quality = {
            **base,
            "artifact": "seed_quality_audit",
            "source_hashes_verified": True,
            "json_only": True,
            "preview_records_count": len(records),
            "bounded_seed_only": True,
            "prohibited_result_fields_present": False,
        }
        manifest = {
            **base,
            "artifact": "seed_manifest",
            "allowed_data_write_root": f"{ALLOWED_DATA_WRITE_ROOT}/",
            "created_file_paths": [str(path) for path in ALLOWED_FILES],
            "max_files": MAX_FILES,
            "max_bytes": MAX_BYTES,
            "preview_records_count": len(records),
        }
        return [manifest, schema, preview, provenance, quality]

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        allowed = {allowed.resolve() for allowed in self.allowed_paths}
        if path.resolve() not in allowed:
            raise SeedBuildError(f"Unapproved V1.92 write path: {path}")
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
