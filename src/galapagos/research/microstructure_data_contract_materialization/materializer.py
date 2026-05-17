from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ALLOWED_DATA_WRITE_ROOT = Path("data/research/microstructure_contract_materialization/v1_84")
ALLOWED_FILES = [
    ALLOWED_DATA_WRITE_ROOT / "manifest.json",
    ALLOWED_DATA_WRITE_ROOT / "schema_snapshot.json",
    ALLOWED_DATA_WRITE_ROOT / "preview_records.json",
]
MAX_FILES = 3
MAX_BYTES = 20_000
MAX_PREVIEW_RECORDS = 5


class MaterializationError(ValueError):
    """Raised when the V1.84 materialization contract would be violated."""


def _relative(path: Path, root: Path) -> str:
    return str(path.resolve().relative_to(root.resolve()))


class TinyContractMaterializer:
    """Writes only the three V1.84 proof JSON files under the approved root."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()
        self.allowed_root = self.project_root / ALLOWED_DATA_WRITE_ROOT
        self.allowed_paths = [self.project_root / path for path in ALLOWED_FILES]

    def materialize(self, *, approval: dict[str, Any], dryrun: dict[str, Any]) -> dict[str, Any]:
        if not self._approval_is_valid(approval):
            raise MaterializationError("V1.84 materialization requires validated V1.83 approval.")
        self.allowed_root.mkdir(parents=True, exist_ok=True)
        payloads = self._build_payloads(approval=approval, dryrun=dryrun)
        for path, payload in zip(self.allowed_paths, payloads, strict=True):
            self._write_json(path, payload)
        return self.audit_created_files()

    def audit_created_files(self) -> dict[str, Any]:
        existing_set = {path for path in self.allowed_root.glob("*") if path.is_file()}
        existing = [path for path in self.allowed_paths if path in existing_set]
        existing.extend(sorted(path for path in existing_set if path not in set(self.allowed_paths)))
        created_paths = [_relative(path, self.project_root) for path in existing]
        forbidden_paths = [
            path for path in existing if path.resolve() not in {p.resolve() for p in self.allowed_paths}
        ]
        suffixes = {path.suffix.lower() for path in existing}
        total_bytes = sum(path.stat().st_size for path in existing)
        preview_records_count = 0
        preview_path = self.project_root / ALLOWED_DATA_WRITE_ROOT / "preview_records.json"
        if preview_path.exists():
            preview_payload = json.loads(preview_path.read_text(encoding="utf-8"))
            preview_records_count = len(preview_payload.get("preview_records", []))
        return {
            "allowed_data_write_root": f"{ALLOWED_DATA_WRITE_ROOT}/",
            "created_file_paths": created_paths,
            "created_files_count": len(existing),
            "total_data_files_created": len(existing),
            "total_data_bytes_written": total_bytes,
            "preview_records_count": preview_records_count,
            "unapproved_data_write_detected": bool(forbidden_paths),
            "unapproved_data_write_paths": [_relative(path, self.project_root) for path in forbidden_paths],
            "manifest_json_created": (self.project_root / ALLOWED_FILES[0]).exists(),
            "schema_snapshot_json_created": (self.project_root / ALLOWED_FILES[1]).exists(),
            "preview_records_json_created": (self.project_root / ALLOWED_FILES[2]).exists(),
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
            and approval.get("v1_84_authorized") is True
            and approval.get("authorized_future_scope")
            == "tiny_data_contract_materialization_ultra_bounded_no_network_no_full_dataset_no_ml_no_trading"
        )

    def _build_payloads(self, *, approval: dict[str, Any], dryrun: dict[str, Any]) -> list[dict[str, Any]]:
        base = {
            "version": "V1.84",
            "source": "reports_only_v1_82_4_and_v1_83",
            "network_executed": False,
            "ml_signal_validation_executed": False,
            "trading_allowed": False,
        }
        contract_fields = dryrun.get("contract_fields") or dryrun.get("required_contract_fields") or []
        manifest = {
            **base,
            "artifact": "manifest",
            "approval_source_version": "V1.83",
            "dryrun_source_version": "V1.82.4",
            "approval_source_verified": True,
            "authorized_future_scope": approval.get("authorized_future_scope"),
            "max_files": MAX_FILES,
            "max_bytes": MAX_BYTES,
            "max_preview_records": MAX_PREVIEW_RECORDS,
        }
        schema_snapshot = {
            **base,
            "artifact": "schema_snapshot",
            "schema_source": "microstructure_data_contract_dryrun_contract_v1_82_4",
            "contract_fields": contract_fields[:25] if isinstance(contract_fields, list) else [],
            "field_count_snapshot": len(contract_fields) if isinstance(contract_fields, list) else 0,
            "forbidden_file_types": ["parquet", "csv", "sqlite", "jsonl", "db"],
        }
        preview_records = {
            **base,
            "artifact": "preview_records",
            "preview_records_count": 3,
            "preview_records": [
                {"record_id": "v1_84_preview_001", "source": "dryrun_report", "materialized": False},
                {"record_id": "v1_84_preview_002", "source": "approval_report", "materialized": False},
                {"record_id": "v1_84_preview_003", "source": "contract_snapshot", "materialized": False},
            ],
        }
        return [manifest, schema_snapshot, preview_records]

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        if path.resolve() not in {allowed.resolve() for allowed in self.allowed_paths}:
            raise MaterializationError(f"Unapproved V1.84 write path: {path}")
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
