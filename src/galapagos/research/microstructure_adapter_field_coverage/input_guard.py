from __future__ import annotations
from typing import Dict, Any

class InputGuard:
    def __init__(self, data: Dict[str, Any]):
        self.data = data

    def validate(self) -> Dict[str, Any]:
        required_keys = [
            "contract_approval_summary",
            "required_field_coverage",
            "adapter_field_mapping",
            "required_field_spec"
        ]
        
        missing = [k for k in required_keys if self.data.get(k) is None]
        
        return {
            "status": "PASSED" if not missing else "FAILED",
            "missing_inputs": missing,
            "network_disabled": True,
            "dry_run_only": True
        }
