"""Load and merge regime feature diagnostic inputs."""
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

def load_diagnostic_inputs(
    *,
    predictions_path: str | Path,
    dataset_path: str | Path,
    dataset_alpha_path: str | Path | None = None,
    intrabar_path: str | Path,
    payoff_target_summary_path: str | Path,
    payoff_failure_summary_path: str | Path,
    ev_degradation_summary_path: str | Path,
    canonical_summary_path: str | Path,
) -> dict[str, Any]:
    """Load inputs and diagnostic summaries for V1.43."""
    paths = {
        "pred": Path(predictions_path),
        "ds": Path(dataset_path),
        "ib": Path(intrabar_path),
        "payoff": Path(payoff_target_summary_path),
        "fail": Path(payoff_failure_summary_path),
        "ev": Path(ev_degradation_summary_path),
        "canonical": Path(canonical_summary_path),
    }
    if dataset_alpha_path:
        paths["alpha"] = Path(dataset_alpha_path)

    missing = [str(p) for p in paths.values() if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required diagnostic inputs: {missing}")

    if any(_looks_mock_or_scratch(p) for p in paths.values()):
        raise ValueError("Mock or scratch path detected in research inputs")

    predictions = pd.read_parquet(paths["pred"])
    dataset = pd.read_parquet(paths["ds"])
    intrabar = pd.read_parquet(paths["ib"])
    dataset_alpha = pd.read_parquet(paths["alpha"]) if "alpha" in paths else None
    
    payoff_summary = _load_json(paths["payoff"])
    payoff_failure_summary = _load_json(paths["fail"])
    ev_degradation_summary = _load_json(paths["ev"])
    canonical_summary = _load_json(paths["canonical"])

    predictions["timestamp"] = _normalize_timestamp(predictions["timestamp"])
    dataset["timestamp"] = _normalize_timestamp(dataset["timestamp"])
    if "timestamp" in intrabar.columns:
        intrabar["timestamp"] = _normalize_timestamp(intrabar["timestamp"])
    if dataset_alpha is not None:
        dataset_alpha["timestamp"] = _normalize_timestamp(dataset_alpha["timestamp"])

    rebuilt_predictions, _ = rebuild_canonical_ev_features(predictions.copy())
    analysis_frame = build_diagnostic_analysis_frame(rebuilt_predictions, dataset, dataset_alpha)

    return {
        "predictions": predictions,
        "dataset": dataset,
        "dataset_alpha": dataset_alpha,
        "intrabar": intrabar,
        "analysis_frame": analysis_frame,
        "payoff_summary": payoff_summary,
        "payoff_failure_summary": payoff_failure_summary,
        "ev_degradation_summary": ev_degradation_summary,
        "canonical_summary": canonical_summary,
    }

def build_diagnostic_analysis_frame(
    predictions: pd.DataFrame, 
    dataset: pd.DataFrame,
    dataset_alpha: pd.DataFrame | None = None
) -> pd.DataFrame:
    """Merge predictions with full research features and outcomes."""
    frame = predictions.copy()
    research = dataset.copy()
    
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    research["timestamp"] = pd.to_datetime(research["timestamp"], utc=True)

    # Include all features for inventory and shift analysis
    # But identify forbidden outcome columns
    merged = frame.merge(research, on="timestamp", how="left", suffixes=("", "_ds"))
    
    if dataset_alpha is not None:
        dataset_alpha["timestamp"] = pd.to_datetime(dataset_alpha["timestamp"], utc=True)
        # Merge alpha scores if available
        alpha_cols = [c for c in dataset_alpha.columns if c not in merged.columns or c == "timestamp"]
        merged = merged.merge(dataset_alpha[alpha_cols], on="timestamp", how="left")

    merged["timestamp_year"] = merged["timestamp"].dt.year
    merged["timestamp_half"] = (merged["timestamp"].dt.month <= 6).map({True: "H1", False: "H2"})
    merged["period"] = merged["timestamp_year"].astype(str) + "_" + merged["timestamp_half"]
    
    return merged
