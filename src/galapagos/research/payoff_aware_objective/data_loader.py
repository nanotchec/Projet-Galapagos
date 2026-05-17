"""Load and merge payoff-aware objective research inputs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.research.ev_net_research.canonical_ev_feature_rebuilder import (
    rebuild_canonical_ev_features,
)

from .objective_schema import get_causal_feature_columns, get_categorical_feature_columns


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _looks_mock_or_scratch(path: Path) -> bool:
    lowered = str(path).lower()
    return any(token in lowered for token in ["mock", "scratch", "/dev/null", ".gemini/antigravity/brain"])


def _normalize_timestamp(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, utc=True)


def load_inputs(
    *,
    predictions_path: str | Path,
    dataset_path: str | Path,
    intrabar_path: str | Path,
    diagnostic_summary_path: str | Path,
    ev_summary_path: str | Path,
    canonical_summary_path: str | Path,
) -> dict[str, Any]:
    """Load real inputs and the diagnostic summaries required for V1.40."""
    pred_path = Path(predictions_path)
    dataset_path = Path(dataset_path)
    intrabar_path = Path(intrabar_path)
    diag_path = Path(diagnostic_summary_path)
    ev_path = Path(ev_summary_path)
    canonical_path = Path(canonical_summary_path)
    missing = [str(path) for path in [pred_path, dataset_path, intrabar_path, diag_path, ev_path, canonical_path] if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required payoff objective inputs: {missing}")
    if any(_looks_mock_or_scratch(path) for path in [pred_path, dataset_path, intrabar_path]):
        raise ValueError("Mock or scratch path detected in payoff objective inputs")

    predictions = pd.read_parquet(pred_path)
    dataset = pd.read_parquet(dataset_path)
    intrabar = pd.read_parquet(intrabar_path)
    diagnostic_summary = _load_json(diag_path)
    ev_summary = _load_json(ev_path)
    canonical_summary = _load_json(canonical_path)

    predictions["timestamp"] = _normalize_timestamp(predictions["timestamp"])
    dataset["timestamp"] = _normalize_timestamp(dataset["timestamp"])
    if "available_timestamp" in dataset.columns:
        dataset["available_timestamp"] = _normalize_timestamp(dataset["available_timestamp"])
    if "timestamp" in intrabar.columns:
        intrabar["timestamp"] = _normalize_timestamp(intrabar["timestamp"])

    rebuilt_predictions, rebuild_meta = rebuild_canonical_ev_features(predictions.copy())
    merged = build_analysis_frame(
        rebuilt_predictions,
        dataset,
    )
    return {
        "predictions": predictions,
        "dataset": dataset,
        "intrabar": intrabar,
        "rebuilt_predictions": rebuilt_predictions,
        "analysis_frame": merged,
        "rebuild_meta": rebuild_meta,
        "diagnostic_summary": diagnostic_summary,
        "ev_summary": ev_summary,
        "canonical_summary": canonical_summary,
    }


def build_analysis_frame(predictions: pd.DataFrame, dataset: pd.DataFrame) -> pd.DataFrame:
    """Merge prediction rows with causal research features."""
    frame = predictions.copy()
    frame["timestamp"] = _normalize_timestamp(frame["timestamp"])
    research = dataset.copy()
    research["timestamp"] = _normalize_timestamp(research["timestamp"])
    feature_columns = [
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "combined_alpha_score",
        "combined_alpha_score_no_derivatives",
        "combined_alpha_score_no_macro",
        "ohlcv_only_alpha_score",
        "macro_derivatives_score",
        "ohlcv_momentum_score",
        "ohlcv_breakout_score",
        "volatility_quality_score",
        "macro_regime_score",
        "cost_penalty_score",
        "crowded_trade_penalty",
        "missing_data_penalty",
        "volume_quality_score",
        "derivatives_regime_score",
        "derivatives_crowding_score",
        "derivatives_leverage_score",
        "derivatives_score",
        "funding_rate_zscore_30d",
        "funding_rate_zscore_90d",
        "open_interest_zscore_30d",
        "open_interest_zscore_90d",
        "premium_zscore_30d",
        "taker_imbalance_zscore",
        "long_short_ratio_zscore",
        "price_oi_confirmation",
        "price_oi_divergence",
        "funding_extreme_positive",
        "funding_extreme_negative",
        "macro_regime",
        "derivatives_risk_regime",
        "volatility_regime",
        "trend_regime",
        "vol_regime_vix",
        "derivatives_available_count",
        "derivatives_missing_count",
    ]
    feature_columns = [column for column in feature_columns if column in research.columns]
    context = research[feature_columns].drop_duplicates("timestamp")
    merged = frame.merge(context, on="timestamp", how="left", suffixes=("", "_research"))
    merged = merged.sort_values(["timestamp", "model_name", "target"]).reset_index(drop=True)
    merged["analysis_row_id"] = range(len(merged))
    if "ev_proxy_ready" in merged.columns:
        merged["analysis_ready"] = merged["ev_proxy_ready"].fillna(False).astype(bool)
        merged["analysis_subset_reason"] = merged["analysis_ready"].map(
            lambda value: "ev_proxy_ready" if value else "warmup_blocked"
        )
    else:
        # The current prediction parquet does not expose ev_proxy_ready.
        # For exploratory diagnostics we keep the full real-data universe rather than
        # dropping every row and silently turning the analysis into an empty frame.
        merged["analysis_ready"] = pd.Series(True, index=merged.index, dtype=bool)
        merged["analysis_subset_reason"] = "ev_proxy_ready_missing"
    merged["timestamp_month"] = merged["timestamp"].dt.to_period("M").astype(str)
    merged["timestamp_year"] = merged["timestamp"].dt.year
    merged["timestamp_half"] = merged["timestamp"].dt.to_period("Q").astype(str)
    merged["causal_feature_count"] = len(
        get_causal_feature_columns(merged.columns)
    )
    merged["categorical_feature_count"] = len(
        get_categorical_feature_columns(merged.columns)
    )
    return merged
