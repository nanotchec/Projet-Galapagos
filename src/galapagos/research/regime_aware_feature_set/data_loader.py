"""Data loader for V1.44 research."""
from __future__ import annotations

import pandas as pd
from pathlib import Path
from typing import Any

def load_v1_44_data(
    predictions_path: str,
    dataset_path: str,
    dataset_alpha_path: str,
    intrabar_path: str
) -> dict[str, pd.DataFrame]:
    """Load all necessary dataframes for regime-aware feature research."""
    
    results = {}
    
    # 1. Base Predictions (V1.16.3)
    if not Path(predictions_path).exists():
        raise FileNotFoundError(f"Predictions not found: {predictions_path}")
    results["df_preds"] = pd.read_parquet(predictions_path)
    
    # 2. Research Dataset
    if not Path(dataset_path).exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")
    results["df_dataset"] = pd.read_parquet(dataset_path)
    
    # 3. Dataset with Alpha Scores
    if not Path(dataset_alpha_path).exists():
        raise FileNotFoundError(f"Alpha dataset not found: {dataset_alpha_path}")
    results["df_alpha"] = pd.read_parquet(dataset_alpha_path)
    
    # 4. Intrabar Data
    if not Path(intrabar_path).exists():
        raise FileNotFoundError(f"Intrabar data not found: {intrabar_path}")
    results["df_intrabar"] = pd.read_parquet(intrabar_path)
    
    return results

def load_v1_43_summary(summary_path: str) -> dict[str, Any]:
    """Load the summary of the previous version."""
    import json
    if not Path(summary_path).exists():
        raise FileNotFoundError(f"V1.43.4 summary not found: {summary_path}")
    return json.loads(Path(summary_path).read_text(encoding="utf-8"))
