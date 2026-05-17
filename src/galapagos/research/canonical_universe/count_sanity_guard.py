from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.research.report_models import write_research_report

EXPECTED_V1_36_8_RAW = 171648
EXPECTED_V1_36_8_CANONICAL = 171648
MIN_ACCEPTABLE_ROWS = 100000

def check_count_sanity(
    raw_prediction_rows: int,
    canonical_opportunity_rows: int,
    selection_dataset_rows: int,
    outcome_dataset_rows: int,
    opportunity_index_rows: int,
    version: str = "v1.37.1"
) -> dict[str, Any]:
    
    issues = []
    
    counts = {
        "raw_prediction_rows": raw_prediction_rows,
        "canonical_opportunity_rows": canonical_opportunity_rows,
        "selection_dataset_rows": selection_dataset_rows,
        "outcome_dataset_rows": outcome_dataset_rows,
        "opportunity_index_rows": opportunity_index_rows,
    }
    
    # 1. Reject mock size
    for name, val in counts.items():
        if val == 100:
            issues.append(f"Mock size detected: {name} = 100")
        if val < MIN_ACCEPTABLE_ROWS:
            issues.append(f"Suspiciously low count: {name} = {val} (min {MIN_ACCEPTABLE_ROWS})")

    # 2. Compare with V1.36.8 if possible
    count_match_v1_36_8 = (raw_prediction_rows == EXPECTED_V1_36_8_RAW) and (canonical_opportunity_rows == EXPECTED_V1_36_8_CANONICAL)
    if not count_match_v1_36_8:
        issues.append(f"Count mismatch with V1.36.8 reference (Expected Raw/Canonical: {EXPECTED_V1_36_8_RAW})")

    passed = len(issues) == 0
    status = "CANONICAL_COUNT_SANITY_GUARD_PASSED" if passed else "CANONICAL_COUNT_SANITY_GUARD_FAILED"
    
    payload = {
        "expected_raw_prediction_rows_from_v1_36_8": EXPECTED_V1_36_8_RAW,
        "observed_raw_prediction_rows": raw_prediction_rows,
        "expected_canonical_opportunity_rows_from_v1_36_8": EXPECTED_V1_36_8_CANONICAL,
        "observed_canonical_opportunity_rows": canonical_opportunity_rows,
        "selection_dataset_rows": selection_dataset_rows,
        "outcome_dataset_rows": outcome_dataset_rows,
        "opportunity_index_rows": opportunity_index_rows,
        "count_match_v1_36_8": count_match_v1_36_8,
        "suspicious_mock_count_detected": any(v == 100 for v in counts.values()),
        "count_sanity_guard_status": status,
        "issues": issues
    }
    
    write_research_report(
        name=f"canonical_count_sanity_guard_{version.replace('.', '_')}",
        payload=payload,
        title=f"Canonical Count Sanity Guard {version}",
        lines=[
            f"Status: {status}",
            f"V1.36.8 Match: {count_match_v1_36_8}",
            f"Raw Rows: {raw_prediction_rows}",
            f"Canonical Rows: {canonical_opportunity_rows}"
        ],
        output_dir="reports/research"
    )
    
    return payload
