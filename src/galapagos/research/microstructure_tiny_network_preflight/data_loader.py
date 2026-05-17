import json
from pathlib import Path
from typing import Any, Dict

class DataLoader:
    def __init__(self, root: Path):
        self.root = root

    def load_previous_state(self, version: str) -> Dict[str, Any]:
        v_norm = version.replace(".", "_").lower()
        summary_p = self.root / f"reports/research/microstructure_human_approval_summary_{v_norm}.json"
        
        if not summary_p.exists():
            # Fallback for even older versions if needed, but here we expect V1.70.2
            summary_p = self.root / f"reports/research/microstructure_pending_tiny_preflight_summary_{v_norm}.json"
            
        if not summary_p.exists():
            raise FileNotFoundError(f"Missing summary at {summary_p}")
        
        with open(summary_p) as f:
            return json.load(f)

    def load_plan(self, version: str) -> Dict[str, Any]:
        v_norm = version.replace(".", "_").lower()
        plan_p = self.root / f"reports/research/microstructure_v1_71_execution_plan_{v_norm}.json"
        if not plan_p.exists():
             return {}
        with open(plan_p) as f:
            return json.load(f)
