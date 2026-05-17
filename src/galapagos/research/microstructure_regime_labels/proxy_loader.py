from __future__ import annotations
import json
from pathlib import Path

def load_proxies(microstructure_summary_path: Path) -> dict:
    with open(microstructure_summary_path, "r") as f:
        summary = json.load(f)
    
    best_candidates = summary.get("best_microstructure_candidates", [])
    return {
        "microstructure_feature_base_version": summary.get("version"),
        "best_microstructure_candidates": best_candidates,
        "proxy_load_status": "MICROSTRUCTURE_PROXY_LOAD_COMPLETED"
    }
