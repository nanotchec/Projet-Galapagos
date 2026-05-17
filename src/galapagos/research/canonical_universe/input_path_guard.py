from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.research.report_models import write_research_report

FORBIDDEN_TOKENS = [
    "mock",
    "scratch",
    "/dev/null",
    "tmp",
    "test",
    ".gemini/antigravity/brain",
]

ALLOWED_PREDICTIONS_PREFIX = "data/gold/ml_predictions/BTC/4h/"
ALLOWED_DATASET_PREFIX = "data/gold/research_dataset/BTC/4h/"
ALLOWED_INTRABAR_PREFIX = "data/silver/intrabar/binance/BTCUSDT/5m/"

def check_input_paths(
    predictions_path: str,
    dataset_path: str,
    intrabar_path: str,
    version: str = "v1.37.1"
) -> dict[str, Any]:
    paths = {
        "predictions_path": predictions_path,
        "dataset_path": dataset_path,
        "intrabar_path": intrabar_path,
    }
    
    issues = []
    
    # Check tokens
    for name, path in paths.items():
        if not path:
            issues.append(f"{name} is empty")
            continue
        for token in FORBIDDEN_TOKENS:
            if token in path:
                issues.append(f"Forbidden token '{token}' found in {name}: {path}")
                
    # Check prefixes
    if not predictions_path.startswith(ALLOWED_PREDICTIONS_PREFIX):
         issues.append(f"predictions_path must start with {ALLOWED_PREDICTIONS_PREFIX}")
    if not dataset_path.startswith(ALLOWED_DATASET_PREFIX):
         issues.append(f"dataset_path must start with {ALLOWED_DATASET_PREFIX}")
    if not intrabar_path.startswith(ALLOWED_INTRABAR_PREFIX):
         issues.append(f"intrabar_path must start with {ALLOWED_INTRABAR_PREFIX}")

    passed = len(issues) == 0
    status = "CANONICAL_INPUT_PATH_GUARD_PASSED" if passed else "CANONICAL_INPUT_PATH_GUARD_FAILED"
    
    payload = {
        **paths,
        "forbidden_path_tokens_found": [iss for iss in issues if "token" in iss],
        "prefix_issues": [iss for iss in issues if "must start with" in iss],
        "paths_are_canonical_real_data": passed,
        "input_path_guard_status": status,
        "issues": issues
    }
    
    write_research_report(
        name=f"canonical_input_path_guard_{version.replace('.', '_')}",
        payload=payload,
        title=f"Canonical Input Path Guard {version}",
        lines=[
            f"Status: {status}",
            f"Paths are canonical real data: {passed}",
            f"Issues found: {len(issues)}"
        ],
        output_dir="reports/research"
    )
    
    return payload
