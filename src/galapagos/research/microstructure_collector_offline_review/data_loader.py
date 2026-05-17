import json
from pathlib import Path
from typing import Dict, Any

class OfflineReviewDataLoader:
    """Loads JSON reports for V1.58 Human Offline Review Gate."""
    
    def __init__(self, reports_root: str = "reports"):
        self.reports_root = Path(reports_root)

    def load_report(self, path: str) -> Dict[str, Any]:
        p = Path(path)
        if not p.exists():
            # Try relative to reports root if not absolute
            p = self.reports_root / path
        
        if not p.exists():
            raise FileNotFoundError(f"Report not found: {path}")
            
        with open(p, "r") as f:
            return json.load(f)

    def load_all_inputs(self, paths: Dict[str, str]) -> Dict[str, Any]:
        data = {}
        for key, path in paths.items():
            data[key] = self.load_report(path)
        return data
