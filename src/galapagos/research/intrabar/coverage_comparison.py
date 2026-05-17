"""Logic for comparing coverage between versions."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def compare_coverage(v_prev_path: str, v_curr_path: str) -> dict[str, Any]:
    """Compare trade ledger coverage between two versions."""
    if not Path(v_prev_path).exists() or not Path(v_curr_path).exists():
        return {"status": "error", "message": "One or both reports missing"}
    
    with open(v_prev_path) as f:
        prev = json.load(f)
    with open(v_curr_path) as f:
        curr = json.load(f)
        
    # Extract evaluated_ratio
    # v1.19.2 report structure: policy_metrics[any_policy][evaluated_ratio]
    p_name = list(curr["policy_metrics"].keys())[0]
    prev_ratio = prev["policy_metrics"][p_name]["evaluated_ratio"]
    curr_ratio = curr["policy_metrics"][p_name]["evaluated_ratio"]
    
    prev_count = prev["policy_metrics"][p_name]["evaluated_count"]
    curr_count = curr["policy_metrics"][p_name]["evaluated_count"]
    
    improvement = curr_ratio / prev_ratio if prev_ratio > 0 else 0
    
    return {
        "previous_version": prev["version"],
        "current_version": curr["version"],
        "previous_evaluated_ratio": prev_ratio,
        "current_evaluated_ratio": curr_ratio,
        "previous_evaluated_count": prev_count,
        "current_evaluated_count": curr_count,
        "improvement_factor": improvement,
        "status": "COVERAGE_IMPROVED" if improvement > 1.1 else "COVERAGE_STILL_TOO_LOW"
    }
