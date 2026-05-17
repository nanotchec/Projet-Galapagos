import json
from pathlib import Path
from typing import Any, Dict

class DataLoader:
    def __init__(self, root: Path):
        self.root = root

    def load_previous_state(self, version: str) -> Dict[str, Any]:
        v_norm = version.replace(".", "_").lower()
        summary_p = self.root / f"reports/research/microstructure_two_request_review_summary_{v_norm}.json"
        if not summary_p.exists():
            summary_p = self.root / f"reports/research/microstructure_bounded_mini_collection_approval_summary_{v_norm}.json"
        
        if not summary_p.exists():
            raise FileNotFoundError(f"Missing summary at {summary_p} or alternative")
        
        with open(summary_p) as f:
            return json.load(f)
