from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.research.microstructure_data_contract_consolidation_readiness import (
    AUTHORIZED_FUTURE_SCOPE,
    ConsolidationPhysicalAuditor,
)

ALLOWED_DATA_WRITE_ROOT = Path("data/research/microstructure_contract_materialization/v1_90")
ALLOWED_FILES = [
    ALLOWED_DATA_WRITE_ROOT / "consolidated_manifest.json",
    ALLOWED_DATA_WRITE_ROOT / "consolidated_schema_snapshot.json",
    ALLOWED_DATA_WRITE_ROOT / "consolidated_quality_summary.json",
]
MAX_FILES = 3
MAX_BYTES = 25_000
FORBIDDEN_SUFFIXES = {".parquet", ".csv", ".sqlite", ".jsonl", ".db"}


class ConsolidationError(ValueError):
    """Raised when V1.90 consolidation would violate its approved scope."""


def _relative(path: Path, root: Path) -> str:
    return str(path.resolve().relative_to(root.resolve()))


class TinyContractConsolidator:
    """Writes only the three V1.90 consolidation JSON files under the approved root."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()
        self.allowed_root = self.project_root / ALLOWED_DATA_WRITE_ROOT
        self.allowed_paths = [self.project_root / path for path in ALLOWED_FILES]

    def consolidate(self, *, approval: dict[str, Any], design: dict[str, Any]) -> dict[str, Any]:
        if not self._approval_is_valid(approval):
            raise ConsolidationError("V1.90 consolidation requires validated V1.89 approval.")
        if not self._design_is_valid(design):
            raise ConsolidationError("V1.90 consolidation requires bounded V1.89 design.")
        pre_audit = ConsolidationPhysicalAuditor(self.project_root).audit()
        if not pre_audit["v1_84_hashes_verified"] or not pre_audit["v1_87_hashes_verified"]:
            raise ConsolidationError("V1.84/V1.87 hash verification failed before write.")
        self.allowed_root.mkdir(parents=True, exist_ok=True)
        payloads = self._build_payloads(approval=approval, design=design, pre_audit=pre_audit)
        for path, payload in zip(self.allowed_paths, payloads, strict=True):
            self._write_json(path, payload)
        post_audit = ConsolidationPhysicalAuditor(self.project_root).audit()
        file_audit = self.audit_created_files()
        file_audit["existing_v1_84_files_modified"] = post_audit["v1_84_hashes_observed"] != pre_audit["v1_84_hashes_observed"]
        file_audit["existing_v1_87_files_modified"] = post_audit["v1_87_hashes_observed"] != pre_audit["v1_87_hashes_observed"]
        file_audit["v1_84_hashes_verified"] = post_audit["v1_84_hashes_verified"]
        file_audit["v1_87_hashes_verified"] = post_audit["v1_87_hashes_verified"]
        return file_audit

    def audit_created_files(self) -> dict[str, Any]:
        existing_set = {path for path in self.allowed_root.glob("*") if path.is_file()}
        allowed_set = {path.resolve() for path in self.allowed_paths}
        existing = [path for path in self.allowed_paths if path in existing_set]
        existing.extend(sorted(path for path in existing_set if path not in set(self.allowed_paths)))
        suffixes = {path.suffix.lower() for path in existing}
        forbidden_paths = [path for path in existing if path.resolve() not in allowed_set]
        total_bytes = sum(path.stat().st_size for path in existing)
        return {
            "allowed_data_write_root": f"{ALLOWED_DATA_WRITE_ROOT}/",
            "created_file_paths": [_relative(path, self.project_root) for path in existing],
            "created_files_count": len(existing),
            "total_new_data_files_created": len(existing),
            "total_data_bytes_written": total_bytes,
            "unapproved_data_write_detected": bool(forbidden_paths),
            "unapproved_data_write_paths": [_relative(path, self.project_root) for path in forbidden_paths],
            "consolidated_manifest_json_created": (self.project_root / ALLOWED_FILES[0]).exists(),
            "consolidated_schema_snapshot_json_created": (self.project_root / ALLOWED_FILES[1]).exists(),
            "consolidated_quality_summary_json_created": (self.project_root / ALLOWED_FILES[2]).exists(),
            "parquet_created": ".parquet" in suffixes,
            "csv_created": ".csv" in suffixes,
            "sqlite_created": ".sqlite" in suffixes,
            "jsonl_created": ".jsonl" in suffixes,
            "db_created": ".db" in suffixes,
        }

    def _approval_is_valid(self, approval: dict[str, Any]) -> bool:
        return (
            approval.get("human_approval_granted") is True
            and approval.get("approval_phrase_match") is True
            and approval.get("v1_90_authorized") is True
            and approval.get("authorized_future_scope") == AUTHORIZED_FUTURE_SCOPE
        )

    def _design_is_valid(self, design: dict[str, Any]) -> bool:
        return (
            design.get("data_contract_v2_designed") is True
            and design.get("consolidation_plan_created") is True
            and design.get("future_consolidation_allowed_root") == f"{ALLOWED_DATA_WRITE_ROOT}/"
            and design.get("future_consolidation_max_files") <= MAX_FILES
            and design.get("future_consolidation_max_bytes") <= MAX_BYTES
            and design.get("future_consolidation_allowed_extensions") == [".json"]
        )

    def _build_payloads(
        self, *, approval: dict[str, Any], design: dict[str, Any], pre_audit: dict[str, Any]
    ) -> list[dict[str, Any]]:
        base = {
            "version": "V1.90",
            "source": "v1_84_v1_87_reports_and_v1_89_approval",
            "network_executed": False,
            "ml_signal_validation_executed": False,
            "trading_allowed": False,
        }
        manifest = {
            **base,
            "artifact": "consolidated_manifest",
            "approval_source_version": "V1.89",
            "authorized_future_scope": approval["authorized_future_scope"],
            "reviewed_materialization_version": "V1.84",
            "reviewed_extension_version": "V1.87.2",
            "max_files": MAX_FILES,
            "max_bytes": MAX_BYTES,
        }
        schema_snapshot = {
            **base,
            "artifact": "consolidated_schema_snapshot",
            "design_source_version": "V1.89",
            "allowed_root": design["future_consolidation_allowed_root"],
            "allowed_extensions": design["future_consolidation_allowed_extensions"],
            "forbidden_extensions": design["future_consolidation_forbidden_extensions"],
        }
        quality_summary = {
            **base,
            "artifact": "consolidated_quality_summary",
            "v1_84_hashes_verified": pre_audit["v1_84_hashes_verified"],
            "v1_87_hashes_verified": pre_audit["v1_87_hashes_verified"],
            "v1_84_files_count": pre_audit["v1_84_files_count"],
            "v1_87_files_count": pre_audit["v1_87_files_count"],
            "full_dataset_created": False,
        }
        return [manifest, schema_snapshot, quality_summary]

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        if path.resolve() not in {allowed.resolve() for allowed in self.allowed_paths}:
            raise ConsolidationError(f"Unapproved V1.90 write path: {path}")
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
