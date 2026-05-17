"""Load and merge inputs for microstructure regime diagnostic V1.49."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))

def _looks_mock_or_scratch(path: Path) -> bool:
    lowered = str(path).lower()
    return any(token in lowered for token in ["mock", "scratch", "/dev/null", ".gemini/antigravity/brain"])

def _normalize_timestamp(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, utc=True)

def load_microstructure_regime_diagnostic_inputs(
    *,
    predictions_path: str | Path,
    dataset_path: str | Path,
    dataset_alpha_path: str | Path | None = None,
    intrabar_path: str | Path,
    microstructure_label_summary_path: str | Path,
    microstructure_label_quality_path: str | Path,
    microstructure_loss_relevance_path: str | Path,
    regime_data_quality_summary_path: str | Path,
    feature_ablation_summary_path: str | Path,
    canonical_summary_path: str | Path,
) -> dict[str, Any]:
    """Load inputs and research summaries for V1.49."""
    paths = {
        "pred": Path(predictions_path),
        "ds": Path(dataset_path),
        "ib": Path(intrabar_path),
        "micro_summary": Path(microstructure_label_summary_path),
        "micro_quality": Path(microstructure_label_quality_path),
        "micro_loss": Path(microstructure_loss_relevance_path),
        "regime_dq": Path(regime_data_quality_summary_path),
        "ablation": Path(feature_ablation_summary_path),
        "canonical": Path(canonical_summary_path),
    }
    if dataset_alpha_path:
        paths["alpha"] = Path(dataset_alpha_path)

    missing = [str(p) for p in paths.values() if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required microstructure regime diagnostic inputs: {missing}")

    if any(_looks_mock_or_scratch(p) for p in paths.values()):
        raise ValueError("Mock or scratch path detected in research inputs")

    predictions = pd.read_parquet(paths["pred"])
    dataset = pd.read_parquet(paths["ds"])
    intrabar = pd.read_parquet(paths["ib"])
    dataset_alpha = pd.read_parquet(paths["alpha"]) if "alpha" in paths else None
    
    micro_summary = _load_json(paths["micro_summary"])
    micro_quality = _load_json(paths["micro_quality"])
    micro_loss = _load_json(paths["micro_loss"])
    regime_dq_summary = _load_json(paths["regime_dq"])
    ablation_summary = _load_json(paths["ablation"])
    canonical_summary = _load_json(paths["canonical"])

    predictions["timestamp"] = _normalize_timestamp(predictions["timestamp"])
    dataset["timestamp"] = _normalize_timestamp(dataset["timestamp"])
    if "timestamp" in intrabar.columns:
        intrabar["timestamp"] = _normalize_timestamp(intrabar["timestamp"])
    if dataset_alpha is not None:
        dataset_alpha["timestamp"] = _normalize_timestamp(dataset_alpha["timestamp"])

    analysis_frame = build_diagnostic_frame(predictions, dataset, dataset_alpha)

    return {
        "predictions": predictions,
        "dataset": dataset,
        "dataset_alpha": dataset_alpha,
        "intrabar": intrabar,
        "analysis_frame": analysis_frame,
        "micro_summary": micro_summary,
        "micro_quality": micro_quality,
        "micro_loss": micro_loss,
        "regime_dq_summary": regime_dq_summary,
        "ablation_summary": ablation_summary,
        "canonical_summary": canonical_summary,
    }

def build_diagnostic_frame(
    predictions: pd.DataFrame, 
    dataset: pd.DataFrame,
    dataset_alpha: pd.DataFrame | None = None
) -> pd.DataFrame:
    """Merge predictions with research features."""
    frame = predictions.copy()
    research = dataset.copy()
    
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    research["timestamp"] = pd.to_datetime(research["timestamp"], utc=True)

    merged = frame.merge(research, on="timestamp", how="left", suffixes=("", "_ds"))
    
    if dataset_alpha is not None:
        dataset_alpha["timestamp"] = pd.to_datetime(dataset_alpha["timestamp"], utc=True)
        alpha_cols = [c for c in dataset_alpha.columns if c not in merged.columns or c == "timestamp"]
        merged = merged.merge(dataset_alpha[alpha_cols], on="timestamp", how="left")

    # V1.49: Calculate microstructure labels if missing
    if "amihud_illiquidity_regime" not in merged.columns:
        # Proxy: abs(return) / volume
        ret = (merged["close"] / merged["open"] - 1).abs()
        amihud = ret / (merged["volume"] + 1e-9)
        merged["amihud_illiquidity_regime"] = pd.qcut(amihud.fillna(0), 3, labels=["low", "mid", "high"]).astype(str)
        
    if "realized_vol_proxy_regime" not in merged.columns:
        # Proxy: (high - low) / open
        vol_proxy = (merged["high"] - merged["low"]) / merged["open"]
        merged["realized_vol_proxy_regime"] = pd.qcut(vol_proxy.fillna(0), 3, labels=["low", "mid", "high"]).astype(str)

    merged["timestamp_year"] = merged["timestamp"].dt.year
    merged["is_2026"] = merged["timestamp_year"] == 2026
    
    return merged
