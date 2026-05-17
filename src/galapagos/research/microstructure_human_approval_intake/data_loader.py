import json
from pathlib import Path
from typing import Any, Dict

class DataLoader:
    def __init__(self, root: Path):
        self.root = root

    def load_previous_state(self, version: str) -> Dict[str, Any]:
        v_norm = version.replace(".", "_").lower()
        if "70" in v_norm:
            summary_p = self.root / f"reports/research/microstructure_human_approval_summary_{v_norm}.json"
        else:
            summary_p = self.root / f"reports/research/microstructure_pending_tiny_preflight_summary_{v_norm}.json"
            
        if not summary_p.exists():
            raise FileNotFoundError(f"Missing summary at {summary_p}")
        
        with open(summary_p) as f:
            return json.load(f)

    def load_audit_data(self, version: str) -> Dict[str, Any]:
        v_norm = version.replace(".", "_").lower()
        if "70" in v_norm:
            audit_p = self.root / f"reports/research/microstructure_human_approval_summary_{v_norm}.json"
        else:
            audit_p = self.root / f"reports/research/microstructure_pending_tiny_preflight_path_portability_audit_{v_norm}.json"
            
        if not audit_p.exists():
             return {}
        with open(audit_p) as f:
            return json.load(f)
