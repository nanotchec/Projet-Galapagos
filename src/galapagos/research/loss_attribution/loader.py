from __future__ import annotations

from typing import Any

import pandas as pd


def load_v1_22_1_baseline(report_path: str) -> dict[str, Any]:
    """Load the V1.22.1 trade ledger summary report."""
    import json
    with open(report_path) as f:
        return json.load(f)

def load_research_context(
    predictions_path: str,
    dataset_path: str,
    intrabar_path: str
) -> dict[str, pd.DataFrame]:
    """Load all necessary parquet files for deep analysis."""
    return {
        "predictions": pd.read_parquet(predictions_path),
        "dataset": pd.read_parquet(dataset_path),
        "intrabar": pd.read_parquet(intrabar_path)
    }
