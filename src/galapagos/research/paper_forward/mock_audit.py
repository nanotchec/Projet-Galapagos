from __future__ import annotations

import os
from pathlib import Path
from typing import Any

def run_mock_audit(package_path: str) -> dict[str, Any]:
    """Scan files for placeholders, mocks, and dummy values, avoiding self-reference false positives."""
    p = Path(package_path)
    if not p.exists():
        return {"status": "PACKAGE_NOT_FOUND", "package": package_path}
    
    forbidden_strings = ["Placeholder", "Mock", "Dummy", "TODO", "FIXME"]
    forbidden_values = [
        "profit_factor = 1.0",
        "top_10_trades_contribution = 0.0",
        "mean_net_pnl_after_cost_pct = 0.005",
        "threshold = 0.5"
    ]
    
    blocking_hits = []
    self_reference_hits = []
    scanned_files = []
    
    for root, _, files in os.walk(p):
        for file in files:
            if not file.endswith(".py"):
                continue
            
            file_path = Path(root) / file
            scanned_files.append(str(file_path))
            content = file_path.read_text()
            
            # Simple check: if this file is mock_audit.py, hits are self-references
            is_self = file_path.name == "mock_audit.py"
            
            for s in forbidden_strings:
                if s in content:
                    hit = {"file": str(file_path), "type": "string", "hit": s}
                    if is_self:
                        self_reference_hits.append(hit)
                    else:
                        blocking_hits.append(hit)
            
            for v in forbidden_values:
                if v in content:
                    hit = {"file": str(file_path), "type": "value", "hit": v}
                    if is_self:
                        self_reference_hits.append(hit)
                    else:
                        blocking_hits.append(hit)
                        
    if blocking_hits:
        status = "PAPER_FORWARD_MOCKS_DETECTED"
    elif self_reference_hits:
        status = "PAPER_FORWARD_SELF_REFERENCE_ONLY"
    else:
        status = "PAPER_FORWARD_NO_MOCKS_DETECTED"
        
    hits = blocking_hits + self_reference_hits
    return {
        "status": status,
        "mock_components_present": len(blocking_hits) > 0,
        "blocking_hits": blocking_hits,
        "self_reference_hits": self_reference_hits,
        "hits": hits,
        "scanned_files_count": len(scanned_files),
        "scanned_files": scanned_files
    }
