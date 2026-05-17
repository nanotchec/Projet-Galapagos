import os
import json
from pathlib import Path
from .safety_guard import SafetyGuard

class Validator:
    def __init__(self):
        self.guard = SafetyGuard()

    def validate(self, summary_data: dict, metrics_data: dict, project_state: dict):
        # 1. Check basic flags
        if not summary_data.get("approval_source_verified"):
            return False, "approval_source_verified must be true"
        if not summary_data.get("human_approval_granted"):
            return False, "human_approval_granted must be true"
        if not summary_data.get("v1_87_authorized"):
            return False, "v1_87_authorized must be true"
        if not summary_data.get("extension_materialization_executed"):
            return False, "extension_materialization_executed must be true"
        if not summary_data.get("tiny_extension_only"):
            return False, "tiny_extension_only must be true"
        if summary_data.get("full_dataset_created"):
            return False, "full_dataset_created must be false"
        if summary_data.get("network_executed"):
            return False, "network_executed must be false"
        if not summary_data.get("data_directory_writes_allowed"):
            return False, "data_directory_writes_allowed must be true"
        if not summary_data.get("data_write_approved"):
            return False, "data_write_approved must be true"
        if summary_data.get("unapproved_data_write_detected"):
            return False, "unapproved_data_write_detected must be false"
        
        # 2. Check limits
        created_files_count = summary_data.get("total_new_data_files_created", 0)
        if created_files_count > self.guard.MAX_FILES:
            return False, f"Too many files created: {created_files_count}"
        
        total_bytes = summary_data.get("total_data_bytes_written", 0)
        if total_bytes > self.guard.MAX_BYTES:
            return False, f"Total data bytes limit exceeded: {total_bytes}"

        if summary_data.get("existing_v1_84_files_modified"):
            return False, "existing_v1_84_files_modified must be false"
        
        # 3. Check forbidden types
        for file_type in ["parquet", "csv", "sqlite", "jsonl", "db"]:
            if summary_data.get(f"{file_type}_created"):
                return False, f"{file_type}_created must be false"
        
        if summary_data.get("dataset_created"):
            return False, "dataset_created must be false"
        if summary_data.get("research_dataset_updated"):
            return False, "research_dataset_updated must be false"

        # 4. Check trading/ML
        if summary_data.get("trading_allowed"):
            return False, "trading_allowed must be false"
        if summary_data.get("real_orders_possible"):
            return False, "real_orders_possible must be false"
        if summary_data.get("ml_signal_validation_executed"):
            return False, "ml_signal_validation_executed must be false"

        # 5. Physical check
        v1_87_dir = Path(self.guard.ALLOWED_DATA_WRITE_ROOT)
        if not v1_87_dir.exists():
            return False, f"Directory {v1_87_dir} does not exist"
        
        actual_files = [f.name for f in v1_87_dir.iterdir() if f.is_file()]
        expected_files = ["extension_manifest.json", "extension_quality_summary.json"]
        
        if sorted(actual_files) != sorted(expected_files):
            return False, f"Actual files {actual_files} do not match expected {expected_files}"

        # 6. Check V1.84 integrity
        import hashlib
        def compute_sha256(path: Path) -> str:
            h = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    h.update(chunk)
            return h.hexdigest()

        v1_84_dir = Path("data/research/microstructure_contract_materialization/v1_84/")
        # Hashes from V1.87.1 audit
        expected_hashes = {
            "manifest.json": "524c43853d97904aadcbd476e955dd5571adecaae5644505a9384e209825aa47",
            "preview_records.json": "2ec5fa4e2911fbb28d6869bd795b1264b9eeb9bc0b5cb531d53e88103f82b01c",
            "schema_snapshot.json": "2ef9706d2be0363b08b61e90585d64c2adb322f16b6317e941d834cffd967638"
        }
        for fname, expected_hash in expected_hashes.items():
            fpath = v1_84_dir / fname
            if not fpath.exists():
                return False, f"V1.84 file {fname} missing"
            actual_hash = compute_sha256(fpath)
            if actual_hash != expected_hash:
                return False, f"V1.84 file {fname} hash mismatch"

        # 7. Alignment check
        if summary_data.get("version") != metrics_data.get("version") or summary_data.get("version") != project_state.get("version"):
            return False, "Version mismatch between reports"

        return True, "All validations passed"
