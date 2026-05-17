import json
from pathlib import Path
from typing import Any, Dict

class V1_79ReportLoader:
    def __init__(self, root: Path):
        self.root = root

    def load_summary(self) -> Dict[str, Any]:
        p = self.root / "reports/research/microstructure_http_status_rerun_summary_v1_79.json"
        if not p.exists():
            raise FileNotFoundError(f"Missing V1.79 summary at {p}")
        with open(p) as f:
            return json.load(f)
            
    def load_response_summary(self) -> Dict[str, Any]:
        p = self.root / "reports/research/microstructure_http_status_response_summary_v1_79.json"
        if not p.exists():
            raise FileNotFoundError(f"Missing V1.79 response summary at {p}")
        with open(p) as f:
            return json.load(f)
            
    def load_safety_audit(self) -> Dict[str, Any]:
        p = self.root / "reports/research/microstructure_http_status_safety_audit_v1_79.json"
        if not p.exists():
            raise FileNotFoundError(f"Missing V1.79 safety audit at {p}")
        with open(p) as f:
            return json.load(f)
            
    def load_no_write_guard(self) -> Dict[str, Any]:
        p = self.root / "reports/research/microstructure_http_status_no_data_write_guard_v1_79.json"
        if not p.exists():
            raise FileNotFoundError(f"Missing V1.79 no-write guard at {p}")
        with open(p) as f:
            return json.load(f)
