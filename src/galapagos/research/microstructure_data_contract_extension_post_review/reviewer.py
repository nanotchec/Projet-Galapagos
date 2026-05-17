from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

V1_84_DATA_ROOT = Path("data/research/microstructure_contract_materialization/v1_84")
V1_87_DATA_ROOT = Path("data/research/microstructure_contract_materialization/v1_87")
EXPECTED_V1_84_FILES = [
    V1_84_DATA_ROOT / "manifest.json",
    V1_84_DATA_ROOT / "schema_snapshot.json",
    V1_84_DATA_ROOT / "preview_records.json",
]
EXPECTED_V1_87_FILES = [
    V1_87_DATA_ROOT / "extension_manifest.json",
    V1_87_DATA_ROOT / "extension_quality_summary.json",
]
EXPECTED_V1_84_HASHES = {
    "manifest.json": "524c43853d97904aadcbd476e955dd5571adecaae5644505a9384e209825aa47",
    "preview_records.json": "2ec5fa4e2911fbb28d6869bd795b1264b9eeb9bc0b5cb531d53e88103f82b01c",
    "schema_snapshot.json": "2ef9706d2be0363b08b61e90585d64c2adb322f16b6317e941d834cffd967638",
}
EXPECTED_V1_87_HASHES = {
    "extension_manifest.json": "525276f53e29bcef84e176dc9d698d37c8a06e2880b7e08965da54aa00e347e4",
    "extension_quality_summary.json": "ddc107e6e862c9b2c3090387279840c587c99a826c96cdebb79c5c7175a2217d",
}
FORBIDDEN_SUFFIXES = {".parquet", ".csv", ".sqlite", ".jsonl", ".db"}
MAX_V1_87_BYTES = 15_000


def _relative(path: Path, root: Path) -> str:
    return str(path.resolve().relative_to(root.resolve()))


def _sha256(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(8192), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


class ExtensionPostReviewReviewer:
    """Audits V1.87 extension artifacts and V1.84 base artifacts without data writes."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()
        self.v1_84_root = self.project_root / V1_84_DATA_ROOT
        self.v1_87_root = self.project_root / V1_87_DATA_ROOT
        self.v1_84_expected = [self.project_root / path for path in EXPECTED_V1_84_FILES]
        self.v1_87_expected = [self.project_root / path for path in EXPECTED_V1_87_FILES]

    def review(self) -> dict[str, Any]:
        v1_84_existing, v1_84_missing, v1_84_unexpected = self._scan(self.v1_84_root, self.v1_84_expected)
        v1_87_existing, v1_87_missing, v1_87_unexpected = self._scan(self.v1_87_root, self.v1_87_expected)
        v1_87_payloads, v1_87_valid = self._load_json(self.v1_87_expected)
        v1_84_hashes = {path.name: _sha256(path) for path in self.v1_84_expected}
        v1_87_hashes = {path.name: _sha256(path) for path in self.v1_87_expected}
        suffixes = {path.suffix.lower() for path in [*v1_84_existing, *v1_87_existing]}
        total_v1_87_bytes = sum(path.stat().st_size for path in v1_87_existing if path.exists())
        manifest = v1_87_payloads.get("extension_manifest") or {}
        return {
            "reviewed_v1_84_root": f"{V1_84_DATA_ROOT}/",
            "reviewed_v1_87_root": f"{V1_87_DATA_ROOT}/",
            "reviewed_v1_84_file_paths": [_relative(path, self.project_root) for path in v1_84_existing],
            "reviewed_v1_87_file_paths": [_relative(path, self.project_root) for path in v1_87_existing],
            "reviewed_v1_84_files_count": len(v1_84_existing),
            "reviewed_v1_87_files_count": len(v1_87_existing),
            "expected_v1_84_files_count": len(self.v1_84_expected),
            "expected_v1_87_files_count": len(self.v1_87_expected),
            "unexpected_v1_84_files_count": len(v1_84_unexpected),
            "unexpected_v1_87_files_count": len(v1_87_unexpected),
            "unexpected_v1_84_file_paths": [_relative(path, self.project_root) for path in v1_84_unexpected],
            "unexpected_v1_87_file_paths": [_relative(path, self.project_root) for path in v1_87_unexpected],
            "missing_v1_84_files_count": len(v1_84_missing),
            "missing_v1_87_files_count": len(v1_87_missing),
            "missing_v1_84_file_paths": [_relative(path, self.project_root) for path in v1_84_missing],
            "missing_v1_87_file_paths": [_relative(path, self.project_root) for path in v1_87_missing],
            "total_v1_87_data_bytes_observed": total_v1_87_bytes,
            "v1_87_extension_manifest_json_valid": v1_87_valid["extension_manifest"],
            "v1_87_extension_quality_summary_json_valid": v1_87_valid["extension_quality_summary"],
            "v1_87_manifest_matches_physical_files": self._manifest_matches(manifest, v1_87_existing),
            "v1_84_hashes_observed": v1_84_hashes,
            "v1_87_hashes_observed": v1_87_hashes,
            "v1_84_hashes_match_expected": v1_84_hashes == EXPECTED_V1_84_HASHES,
            "v1_87_hashes_match_expected": v1_87_hashes == EXPECTED_V1_87_HASHES,
            "parquet_created": ".parquet" in suffixes,
            "csv_created": ".csv" in suffixes,
            "sqlite_created": ".sqlite" in suffixes,
            "jsonl_created": ".jsonl" in suffixes,
            "db_created": ".db" in suffixes,
        }

    def _scan(self, data_root: Path, expected_paths: list[Path]) -> tuple[list[Path], list[Path], list[Path]]:
        expected_set = set(expected_paths)
        existing_set = {path for path in data_root.glob("*") if path.is_file()}
        existing = [path for path in expected_paths if path in existing_set]
        existing.extend(sorted(path for path in existing_set if path not in expected_set))
        missing = [path for path in expected_paths if path not in existing_set]
        unexpected = [path for path in existing if path not in expected_set]
        return existing, missing, unexpected

    def _load_json(self, paths: list[Path]) -> tuple[dict[str, dict[str, Any] | None], dict[str, bool]]:
        payloads: dict[str, dict[str, Any] | None] = {}
        valid_json: dict[str, bool] = {}
        for path in paths:
            key = path.stem
            try:
                payloads[key] = json.loads(path.read_text(encoding="utf-8"))
                valid_json[key] = True
            except (OSError, json.JSONDecodeError, UnicodeDecodeError):
                payloads[key] = None
                valid_json[key] = False
        return payloads, valid_json

    def _manifest_matches(self, manifest: dict[str, Any] | None, existing: list[Path]) -> bool:
        if not isinstance(manifest, dict):
            return False
        return (
            manifest.get("version") == "V1.87"
            and manifest.get("artifact") == "extension_manifest"
            and manifest.get("previous_version") == "V1.84"
            and manifest.get("approval_source") == "V1.86"
            and manifest.get("tiny_extension_only") is True
            and manifest.get("full_dataset_created") is False
            and manifest.get("network_executed") is False
            and {path.name for path in existing} == {"extension_manifest.json", "extension_quality_summary.json"}
        )
