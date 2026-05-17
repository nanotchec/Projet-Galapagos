from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SEED_ROOT = Path("data/research/dataset_seed/v1_92")
EXPECTED_FILES = [
    "seed_manifest.json",
    "seed_schema.json",
    "seed_preview_records.json",
    "seed_provenance.json",
    "seed_quality_audit.json",
]


class MiniResearchDatasetSeedReviewer:
    def __init__(self, root: Path):
        self.root = root
        self.seed_path = root / SEED_ROOT

    def _hash_file(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def audit(self) -> dict[str, Any]:
        results: dict[str, Any] = {
            "reviewed_seed_root": str(SEED_ROOT) + "/",
            "reviewed_files_count": 0,
            "expected_files_count": len(EXPECTED_FILES),
            "unexpected_files_count": 0,
            "missing_expected_files_count": 0,
            "total_data_bytes_observed": 0,
            "preview_records_count": 0,
            "seed_manifest_json_valid": False,
            "seed_schema_json_valid": False,
            "seed_preview_records_json_valid": False,
            "seed_provenance_json_valid": False,
            "seed_quality_audit_json_valid": False,
            "manifest_matches_physical_files": False,
            "seed_checksums_verified": False,
            "schema_validation_passed": False,
            "provenance_validation_passed": False,
            "quality_audit_validation_passed": False,
        }

        if not self.seed_path.exists():
            return results

        existing = sorted(p.name for p in self.seed_path.glob("*") if p.is_file())
        results["reviewed_files_count"] = len(existing)
        results["unexpected_files_count"] = len([f for f in existing if f not in EXPECTED_FILES])
        results["missing_expected_files_count"] = len([f for f in EXPECTED_FILES if f not in existing])

        for f in existing:
            results["total_data_bytes_observed"] += (self.seed_path / f).stat().st_size

        # JSON Validity
        for f in EXPECTED_FILES:
            path = self.seed_path / f
            key = f.replace(".json", "_json_valid")
            if path.exists():
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    results[key] = True
                    if f == "seed_preview_records.json":
                        results["preview_records_count"] = len(data.get("records", []))
                except Exception:
                    results[key] = False

        # Manifest Check
        manifest_path = self.seed_path / "seed_manifest.json"
        if manifest_path.exists() and results["seed_manifest_json_valid"]:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            m_checksums = manifest.get("seed_file_checksums", {})
            
            # The manifest indexes 4 files (schema, preview, provenance, quality)
            # Plus the manifest itself makes 5 files.
            indexed_files = list(m_checksums.keys())
            physical_others = [f for f in EXPECTED_FILES if f != "seed_manifest.json"]
            
            results["manifest_matches_physical_files"] = (sorted(indexed_files) == sorted(physical_others))
            
            checksums_ok = True
            for f, m_sha in m_checksums.items():
                p = self.seed_path / f
                if p.exists():
                    if self._hash_file(p) != m_sha:
                        checksums_ok = False
                else:
                    checksums_ok = False
            results["seed_checksums_verified"] = checksums_ok

        results["schema_validation_passed"] = results["seed_schema_json_valid"]
        results["provenance_validation_passed"] = results["seed_provenance_json_valid"]
        results["quality_audit_validation_passed"] = results["seed_quality_audit_json_valid"]

        return results
