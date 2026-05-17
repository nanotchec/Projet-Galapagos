import json
from pathlib import Path
from typing import Any, Dict

class DataLoader:
    def __init__(self, root: Path):
        self.root = root

    def load_previous_state(self, version: str) -> Dict[str, Any]:
        v_norm = version.replace(".", "_").lower()
        summary_p = self.root / f"reports/research/microstructure_http_status_rerun_summary_{v_norm}.json"
        
        if not summary_p.exists():
            raise FileNotFoundError(f"Missing summary at {summary_p}")
        
        with open(summary_p) as f:
            return json.load(f)
            
    def load_hardening_report(self, version: str) -> Dict[str, Any]:
        v_norm = version.replace(".", "_").lower()
        hard_p = self.root / f"reports/research/microstructure_http_status_capture_hardening_{v_norm}.json"
        
        if not hard_p.exists():
            raise FileNotFoundError(f"Missing hardening report at {hard_p}")
            
        with open(hard_p) as f:
            return json.load(f)
            
    def load_execution_plan(self, version: str) -> Dict[str, Any]:
        v_norm = version.replace(".", "_").lower()
        plan_p = self.root / f"reports/research/microstructure_v1_79_execution_plan_{v_norm}.json"
        
        if not plan_p.exists():
            raise FileNotFoundError(f"Missing execution plan at {plan_p}")
            
        with open(plan_p) as f:
            return json.load(f)
