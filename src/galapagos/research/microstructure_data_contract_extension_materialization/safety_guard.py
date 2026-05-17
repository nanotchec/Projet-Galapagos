import os
import json
from pathlib import Path

class SafetyGuard:
    VERSION = "V1.87"
    VERSION_SUFFIX = "v1_87"
    PREVIOUS_VALIDATED_VERSION = "V1.86"
    APPROVAL_SOURCE_VERSION = "V1.86"
    REVIEWED_MATERIALIZATION_VERSION = "V1.84"
    ALLOWED_DATA_WRITE_ROOT = "data/research/microstructure_contract_materialization/v1_87/"
    MAX_FILES = 2
    MAX_BYTES = 15000
    APPROVAL_PHRASE = "J'approuve V1.87 tiny materialization extension ultra-bornée, sans réseau, sans dataset complet, sans ML, sans trading."

    @classmethod
    def check_approval(cls):
        approval_path = Path("reports/research/microstructure_data_contract_extension_gate_decision_v1_86.json")
        if not approval_path.exists():
            return False, "Missing approval file"
        
        with open(approval_path, "r") as f:
            data = json.load(f)
            
        if data.get("version") != cls.APPROVAL_SOURCE_VERSION:
            return False, f"Invalid approval version: {data.get('version')}"
        
        if not data.get("human_approval_granted"):
            return False, "Human approval not granted in V1.86"
            
        if data.get("approval_phrase_provided") != cls.APPROVAL_PHRASE:
            return False, "Approval phrase mismatch"
            
        return True, "Approval verified"

    @classmethod
    def validate_write_path(cls, file_path: str):
        path = Path(file_path)
        if not str(path).startswith(cls.ALLOWED_DATA_WRITE_ROOT):
            return False, f"Unauthorized write path: {file_path}"
        return True, "Path authorized"

    @classmethod
    def validate_file_type(cls, file_path: str):
        if not file_path.endswith(".json"):
            return False, f"Forbidden file type: {file_path}"
        return True, "File type authorized"

    @classmethod
    def check_limits(cls, current_files_count: int, total_bytes: int):
        if current_files_count > cls.MAX_FILES:
            return False, f"Too many files: {current_files_count} > {cls.MAX_FILES}"
        if total_bytes > cls.MAX_BYTES:
            return False, f"Data bytes limit exceeded: {total_bytes} > {cls.MAX_BYTES}"
        return True, "Limits OK"
