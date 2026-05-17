import json
from pathlib import Path
from typing import Any, Dict

class V1_80Loader:
    def __init__(self, root: Path):
        self.root = root

    def load_summary(self) -> Dict[str, Any]:
        p = self.root / "reports/research/microstructure_data_contract_readiness_summary_v1_80.json"
        if not p.exists():
            raise FileNotFoundError(f"Missing V1.80 summary at {p}")
        with open(p) as f:
            return json.load(f)
            
    def load_approval_gate(self) -> Dict[str, Any]:
        p = self.root / "reports/research/microstructure_data_contract_approval_gate_v1_80.json"
        if not p.exists():
            raise FileNotFoundError(f"Missing V1.80 approval gate at {p}")
        with open(p) as f:
            return json.load(f)
