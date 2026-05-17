from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SEED_ROOT = Path("data/research/dataset_seed/v1_92")
EXPECTED_SEED_FILES = [
    "seed_manifest.json",
    "seed_schema.json",
    "seed_preview_records.json",
    "seed_provenance.json",
    "seed_quality_audit.json",
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SeedReadinessReader:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.seed_root = root / SEED_ROOT

    def read_seed_payloads(self) -> dict[str, Any]:
        return {
            name: json.loads((self.seed_root / name).read_text(encoding="utf-8"))
            for name in EXPECTED_SEED_FILES
        }

    def audit(self) -> dict[str, Any]:
        existing = sorted(path.name for path in self.seed_root.glob("*") if path.is_file()) if self.seed_root.exists() else []
        missing = sorted(set(EXPECTED_SEED_FILES) - set(existing))
        unexpected = sorted(set(existing) - set(EXPECTED_SEED_FILES))
        json_valid = True
        preview_records_count = 0
        payloads: dict[str, Any] = {}
        for name in EXPECTED_SEED_FILES:
            path = self.seed_root / name
            if not path.exists():
                json_valid = False
                continue
            try:
                payloads[name] = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                json_valid = False
        preview = payloads.get("seed_preview_records.json", {})
        if isinstance(preview, dict) and isinstance(preview.get("records"), list):
            preview_records_count = len(preview["records"])
        manifest = payloads.get("seed_manifest.json", {})
        declared = manifest.get("seed_file_checksums") if isinstance(manifest, dict) else {}
        checksums_verified = isinstance(declared, dict)
        if checksums_verified:
            for name in EXPECTED_SEED_FILES:
                if name == "seed_manifest.json":
                    continue
                path = self.seed_root / name
                if not path.exists() or declared.get(name) != _sha256(path):
                    checksums_verified = False
        return {
            "seed_read_only_audit_executed": True,
            "reviewed_seed_root": str(SEED_ROOT) + "/",
            "reviewed_seed_files_count": len(existing),
            "expected_seed_files_count": len(EXPECTED_SEED_FILES),
            "missing_seed_files_count": len(missing),
            "unexpected_seed_files_count": len(unexpected),
            "missing_seed_files": missing,
            "unexpected_seed_files": unexpected,
            "seed_json_valid": json_valid,
            "seed_checksums_verified": checksums_verified,
            "seed_preview_records_count": preview_records_count,
            "seed_total_bytes_observed": sum((self.seed_root / name).stat().st_size for name in existing),
            "existing_seed_files_modified": False,
        }
