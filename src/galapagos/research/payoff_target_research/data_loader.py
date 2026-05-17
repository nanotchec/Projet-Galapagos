"""Load and merge payoff target research inputs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.research.ev_net_research.canonical_ev_feature_rebuilder import (
    rebuild_canonical_ev_features,
)

def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))

def _looks_mock_or_scratch(path: Path) -> bool:
    lowered = str(path).lower()
    return any(token in lowered for token in ["mock", "scratch", "/dev/null", ".gemini/antigravity/brain"])

def _normalize_timestamp(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, utc=True)

def load_research_inputs(
    *,
    predictions_path: str | Path,
    dataset_path: str | Path,
    intrabar_path: str | Path,
    failure_summary_path: str | Path,
    payoff_summary_path: str | Path,
    diagnostic_summary_path: str | Path,
) -> dict[str, Any]:
    """Load real inputs and the diagnostic summaries required for V1.42."""
    pred_path = Path(predictions_path)
    ds_path = Path(dataset_path)
    ib_path = Path(intrabar_path)
    fail_path = Path(failure_summary_path)
    payoff_path = Path(payoff_summary_path)
    diag_path = Path(diagnostic_summary_path)

    missing = [
        str(p) for p in [pred_path, ds_path, ib_path, fail_path, payoff_path, diag_path]
        if not p.exists()
    ]
    if missing:
        raise FileNotFoundError(f"Missing required payoff target research inputs: {missing}")

    if any(_looks_mock_or_scratch(p) for p in [pred_path, ds_path, ib_path]):
        raise ValueError("Mock or scratch path detected in research inputs")

    predictions = pd.read_parquet(pred_path)
    dataset = pd.read_parquet(ds_path)
    intrabar = pd.read_parquet(ib_path)
    failure_summary = _load_json(fail_path)
    payoff_summary = _load_json(payoff_path)
    diagnostic_summary = _load_json(diag_path)

    predictions["timestamp"] = _normalize_timestamp(predictions["timestamp"])
    dataset["timestamp"] = _normalize_timestamp(dataset["timestamp"])
    if "timestamp" in intrabar.columns:
        intrabar["timestamp"] = _normalize_timestamp(intrabar["timestamp"])

    rebuilt_predictions, _ = rebuild_canonical_ev_features(predictions.copy())
    analysis_frame = build_research_analysis_frame(rebuilt_predictions, dataset)

    return {
        "predictions": predictions,
        "dataset": dataset,
        "intrabar": intrabar,
        "analysis_frame": analysis_frame,
        "failure_summary": failure_summary,
        "payoff_summary": payoff_summary,
        "diagnostic_summary": diagnostic_summary,
    }

def build_research_analysis_frame(predictions: pd.DataFrame, dataset: pd.DataFrame) -> pd.DataFrame:
    """Merge prediction rows with research features and outcomes."""
    frame = predictions.copy()
    research = dataset.copy()
    
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    research["timestamp"] = pd.to_datetime(research["timestamp"], utc=True)

    # We need outcomes for labels
    outcome_cols = [c for c in research.columns if "forward_return" in c or c == "timestamp"]
    # We also need some features for regime analysis if available
    feature_cols = ["timestamp", "macro_regime", "volatility_regime", "trend_regime", "cost_proxy"]
    
    needed_cols = list(set(outcome_cols + [c for c in feature_cols if c in research.columns]))
    
    # Avoid duplicate columns during merge
    cols_to_merge = [c for c in needed_cols if c not in frame.columns or c == "timestamp"]
    context = research[cols_to_merge].drop_duplicates("timestamp")
    merged = frame.merge(context, on="timestamp", how="left")
    
    merged["timestamp_year"] = merged["timestamp"].dt.year
    merged["timestamp_half"] = (merged["timestamp"].dt.month <= 6).map({True: "H1", False: "H2"})
    merged["period"] = merged["timestamp_year"].astype(str) + "_" + merged["timestamp_half"]
    
    return merged
