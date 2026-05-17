from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

V1_84_ROOT = Path("data/research/microstructure_contract_materialization/v1_84")
V1_87_ROOT = Path("data/research/microstructure_contract_materialization/v1_87")
V1_90_ROOT = Path("data/research/microstructure_contract_materialization/v1_90")
V1_92_ROOT = Path("data/research/dataset_seed/v1_92")

V1_84_FILES = [
    V1_84_ROOT / "manifest.json",
    V1_84_ROOT / "schema_snapshot.json",
    V1_84_ROOT / "preview_records.json",
]
V1_87_FILES = [
    V1_87_ROOT / "extension_manifest.json",
    V1_87_ROOT / "extension_quality_summary.json",
]
V1_90_FILES = [
    V1_90_ROOT / "consolidated_manifest.json",
    V1_90_ROOT / "consolidated_schema_snapshot.json",
    V1_90_ROOT / "consolidated_quality_summary.json",
]
V1_92_FILES = [
    V1_92_ROOT / "seed_manifest.json",
    V1_92_ROOT / "seed_schema.json",
    V1_92_ROOT / "seed_preview_records.json",
    V1_92_ROOT / "seed_provenance.json",
    V1_92_ROOT / "seed_quality_audit.json",
]

EXPECTED_V1_84_HASHES = {
    "manifest.json": "524c43853d97904aadcbd476e955dd5571adecaae5644505a9384e209825aa47",
    "schema_snapshot.json": "2ef9706d2be0363b08b61e90585d64c2adb322f16b6317e941d834cffd967638",
    "preview_records.json": "2ec5fa4e2911fbb28d6869bd795b1264b9eeb9bc0b5cb531d53e88103f82b01c",
}
EXPECTED_V1_87_HASHES = {
    "extension_manifest.json": "525276f53e29bcef84e176dc9d698d37c8a06e2880b7e08965da54aa00e347e4",
    "extension_quality_summary.json": "ddc107e6e862c9b2c3090387279840c587c99a826c96cdebb79c5c7175a2217d",
}
FORBIDDEN_SUFFIXES = {".parquet", ".csv", ".sqlite", ".jsonl", ".db"}


def sha256_file(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(8192), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def json_valid(path: Path) -> bool:
    try:
        json.loads(path.read_text(encoding="utf-8"))
        return True
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False


class MiniResearchDatasetSeedPhysicalAuditor:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()

    def audit_existing_sources(self) -> dict[str, Any]:
        v1_84_hashes = self._observed_hashes(V1_84_FILES)
        v1_87_hashes = self._observed_hashes(V1_87_FILES)
        v1_90_hashes = self._observed_hashes(V1_90_FILES)
        v1_84_existing, v1_84_extra = self._scan(V1_84_ROOT, V1_84_FILES)
        v1_87_existing, v1_87_extra = self._scan(V1_87_ROOT, V1_87_FILES)
        v1_90_existing, v1_90_extra = self._scan(V1_90_ROOT, V1_90_FILES)
        suffixes = {path.suffix.lower() for path in [*v1_84_existing, *v1_87_existing, *v1_90_existing]}
        return {
            "v1_84_files_count": len(v1_84_existing),
            "v1_87_files_count": len(v1_87_existing),
            "v1_90_files_count": len(v1_90_existing),
            "v1_84_hashes_observed": v1_84_hashes,
            "v1_87_hashes_observed": v1_87_hashes,
            "v1_90_hashes_observed": v1_90_hashes,
            "v1_84_hashes_verified": v1_84_hashes == EXPECTED_V1_84_HASHES,
            "v1_87_hashes_verified": v1_87_hashes == EXPECTED_V1_87_HASHES,
            "v1_90_hashes_verified": len(v1_90_hashes) == len(V1_90_FILES) and all(v1_90_hashes.values()),
            "v1_84_json_valid": all(json_valid(self.project_root / path) for path in V1_84_FILES),
            "v1_87_json_valid": all(json_valid(self.project_root / path) for path in V1_87_FILES),
            "v1_90_json_valid": all(json_valid(self.project_root / path) for path in V1_90_FILES),
            "v1_84_unexpected_files_count": len(v1_84_extra),
            "v1_87_unexpected_files_count": len(v1_87_extra),
            "v1_90_unexpected_files_count": len(v1_90_extra),
            "forbidden_file_types_detected": bool(suffixes & FORBIDDEN_SUFFIXES),
        }

    def audit_seed_outputs(
        self,
        *,
        pre_v1_84_hashes: dict[str, str | None] | None = None,
        pre_v1_87_hashes: dict[str, str | None] | None = None,
        pre_v1_90_hashes: dict[str, str | None] | None = None,
    ) -> dict[str, Any]:
        scanned_existing, extra = self._scan(V1_92_ROOT, V1_92_FILES)
        existing = [self.project_root / path for path in V1_92_FILES if (self.project_root / path).exists()]
        existing.extend(path for path in scanned_existing if path not in existing)
        suffixes = {path.suffix.lower() for path in existing}
        total_bytes = sum(path.stat().st_size for path in existing)
        seed_hashes = self._observed_hashes(V1_92_FILES)
        source = self.audit_existing_sources()
        return {
            "allowed_data_write_root": "data/research/dataset_seed/v1_92/",
            "created_file_paths": [str(path.relative_to(self.project_root)) for path in existing],
            "created_files_count": len(existing),
            "total_new_data_files_created": len(existing),
            "total_data_bytes_written": total_bytes,
            "preview_records_count": self._preview_records_count(),
            "seed_file_hashes_observed": seed_hashes,
            "seed_json_valid": all(json_valid(self.project_root / path) for path in V1_92_FILES),
            "unapproved_data_write_detected": len(extra) > 0,
            "unapproved_data_write_paths": [str(path.relative_to(self.project_root)) for path in extra],
            "seed_manifest_json_created": (self.project_root / V1_92_FILES[0]).exists(),
            "seed_schema_json_created": (self.project_root / V1_92_FILES[1]).exists(),
            "seed_preview_records_json_created": (self.project_root / V1_92_FILES[2]).exists(),
            "seed_provenance_json_created": (self.project_root / V1_92_FILES[3]).exists(),
            "seed_quality_audit_json_created": (self.project_root / V1_92_FILES[4]).exists(),
            "parquet_created": ".parquet" in suffixes,
            "csv_created": ".csv" in suffixes,
            "sqlite_created": ".sqlite" in suffixes,
            "jsonl_created": ".jsonl" in suffixes,
            "db_created": ".db" in suffixes,
            "existing_v1_84_files_modified": (
                pre_v1_84_hashes is not None and source["v1_84_hashes_observed"] != pre_v1_84_hashes
            ),
            "existing_v1_87_files_modified": (
                pre_v1_87_hashes is not None and source["v1_87_hashes_observed"] != pre_v1_87_hashes
            ),
            "existing_v1_90_files_modified": (
                pre_v1_90_hashes is not None and source["v1_90_hashes_observed"] != pre_v1_90_hashes
            ),
            **source,
        }

    def _preview_records_count(self) -> int:
        path = self.project_root / V1_92_ROOT / "seed_preview_records.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return -1
        records = data.get("records") if isinstance(data, dict) else data
        return len(records) if isinstance(records, list) else -1

    def _observed_hashes(self, rel_paths: list[Path]) -> dict[str, str | None]:
        return {path.name: sha256_file(self.project_root / path) for path in rel_paths}

    def _scan(self, rel_root: Path, expected: list[Path]) -> tuple[list[Path], list[Path]]:
        root = self.project_root / rel_root
        expected_abs = {self.project_root / path for path in expected}
        existing = sorted(path for path in root.glob("*") if path.is_file()) if root.exists() else []
        extra = [path for path in existing if path not in expected_abs]
        return existing, extra
