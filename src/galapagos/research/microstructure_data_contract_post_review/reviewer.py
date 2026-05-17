from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REVIEWED_DATA_ROOT = Path("data/research/microstructure_contract_materialization/v1_84")
EXPECTED_DATA_FILES = [
    REVIEWED_DATA_ROOT / "manifest.json",
    REVIEWED_DATA_ROOT / "schema_snapshot.json",
    REVIEWED_DATA_ROOT / "preview_records.json",
]
FORBIDDEN_SUFFIXES = {".parquet", ".csv", ".sqlite", ".jsonl", ".db"}
MAX_BYTES = 20_000
MAX_PREVIEW_RECORDS = 5


def _relative(path: Path, root: Path) -> str:
    return str(path.resolve().relative_to(root.resolve()))


class PostMaterializationReviewer:
    """Reads and audits the V1.84 physical artifacts without writing to data."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()
        self.reviewed_root = self.project_root / REVIEWED_DATA_ROOT
        self.expected_paths = [self.project_root / path for path in EXPECTED_DATA_FILES]

    def review(self, *, dryrun_contract: dict[str, Any]) -> dict[str, Any]:
        existing_set = {path for path in self.reviewed_root.glob("*") if path.is_file()}
        expected_set = set(self.expected_paths)
        existing = [path for path in self.expected_paths if path in existing_set]
        existing.extend(sorted(path for path in existing_set if path not in expected_set))
        missing = [path for path in self.expected_paths if path not in existing_set]
        unexpected = [path for path in existing if path not in expected_set]
        payloads: dict[str, dict[str, Any] | None] = {}
        valid_json: dict[str, bool] = {}
        for path in self.expected_paths:
            key = path.stem
            try:
                payloads[key] = json.loads(path.read_text(encoding="utf-8"))
                valid_json[key] = True
            except (OSError, json.JSONDecodeError, UnicodeDecodeError):
                payloads[key] = None
                valid_json[key] = False
        suffixes = {path.suffix.lower() for path in existing}
        total_bytes = sum(path.stat().st_size for path in existing)
        preview = payloads.get("preview_records") or {}
        preview_records = preview.get("preview_records", []) if isinstance(preview, dict) else []
        manifest = payloads.get("manifest") or {}
        schema_snapshot = payloads.get("schema_snapshot") or {}
        return {
            "reviewed_data_root": f"{REVIEWED_DATA_ROOT}/",
            "reviewed_file_paths": [_relative(path, self.project_root) for path in existing],
            "expected_file_paths": [str(path) for path in EXPECTED_DATA_FILES],
            "reviewed_files_count": len(existing),
            "expected_files_count": len(self.expected_paths),
            "unexpected_files_count": len(unexpected),
            "unexpected_file_paths": [_relative(path, self.project_root) for path in unexpected],
            "missing_expected_files_count": len(missing),
            "missing_expected_file_paths": [_relative(path, self.project_root) for path in missing],
            "total_data_bytes_observed": total_bytes,
            "preview_records_count": len(preview_records),
            "manifest_json_valid": valid_json["manifest"],
            "schema_snapshot_json_valid": valid_json["schema_snapshot"],
            "preview_records_json_valid": valid_json["preview_records"],
            "manifest_matches_physical_files": self._manifest_matches(manifest, existing),
            "schema_snapshot_matches_contract": self._schema_matches_contract(schema_snapshot, dryrun_contract),
            "parquet_created": ".parquet" in suffixes,
            "csv_created": ".csv" in suffixes,
            "sqlite_created": ".sqlite" in suffixes,
            "jsonl_created": ".jsonl" in suffixes,
            "db_created": ".db" in suffixes,
        }

    def _manifest_matches(self, manifest: dict[str, Any] | None, existing: list[Path]) -> bool:
        if not isinstance(manifest, dict):
            return False
        return (
            manifest.get("version") == "V1.84"
            and manifest.get("artifact") == "manifest"
            and manifest.get("max_files") == 3
            and manifest.get("max_bytes") == MAX_BYTES
            and manifest.get("max_preview_records") == MAX_PREVIEW_RECORDS
            and {path.name for path in existing} == {"manifest.json", "schema_snapshot.json", "preview_records.json"}
        )

    def _schema_matches_contract(self, schema_snapshot: dict[str, Any] | None, dryrun_contract: dict[str, Any]) -> bool:
        if not isinstance(schema_snapshot, dict):
            return False
        if schema_snapshot.get("schema_source") != "microstructure_data_contract_dryrun_contract_v1_82_4":
            return False
        dryrun_fields = dryrun_contract.get("contract_fields")
        if isinstance(dryrun_fields, list):
            return schema_snapshot.get("contract_fields") == dryrun_fields[:25]
        dryrun_schema = dryrun_contract.get("schema")
        snapshot_fields = schema_snapshot.get("contract_fields")
        return isinstance(dryrun_schema, dict) and snapshot_fields == []
