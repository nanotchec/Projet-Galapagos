"""Audit JSON reports for non-finite values (NaN, Inf)."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

def audit_json_finiteness(directory: str | Path, pattern: str = "*.json") -> dict[str, Any]:
    """Scan all JSON files in a directory for non-finite values."""
    path = Path(directory)
    json_files = list(path.glob(pattern))
    
    issues = []
    affected_reports = []
    total_nan = 0
    total_inf = 0
    
    for jf in json_files:
        try:
            content = json.loads(jf.read_text(encoding="utf-8"))
            file_nan, file_inf = _scan_recursive(content)
            if file_nan > 0 or file_inf > 0:
                issues.append(f"{jf.name}: found {file_nan} NaN and {file_inf} Inf")
                affected_reports.append(jf.name)
                total_nan += file_nan
                total_inf += file_inf
        except Exception as e:
            issues.append(f"{jf.name}: failed to parse ({e})")
            
    status = "PAYOFF_TARGET_JSON_FINITE_PASSED" if total_nan == 0 and total_inf == 0 else "PAYOFF_TARGET_JSON_FINITE_FAILED"
    
    return {
        "status": status,
        "nan_count": total_nan,
        "infinity_count": total_inf,
        "affected_reports": affected_reports,
        "all_json_values_finite": bool(total_nan == 0 and total_inf == 0),
        "issues": issues
    }

def _scan_recursive(obj: Any) -> tuple[int, int]:
    nan_count = 0
    inf_count = 0
    
    if isinstance(obj, dict):
        for v in obj.values():
            n, i = _scan_recursive(v)
            nan_count += n
            inf_count += i
    elif isinstance(obj, list):
        for v in obj:
            n, i = _scan_recursive(v)
            nan_count += n
            inf_count += i
    elif isinstance(obj, float):
        if math.isnan(obj):
            nan_count += 1
        elif math.isinf(obj):
            inf_count += 1
            
    return nan_count, inf_count
