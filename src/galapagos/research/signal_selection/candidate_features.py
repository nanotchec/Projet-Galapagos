"""Build candidate-level features for cost-aware signal selection."""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from galapagos.research.trade_ledger.schema import TradeCandidate, TradeSimulationResult

from .cost_thresholds import DEFAULT_COST_PCT, cost_to_move_ratio, cost_viability_flags


def _to_utc_series(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, utc=True)


def _to_utc_timestamp(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo:
        return timestamp.tz_convert("UTC")
    return timestamp.tz_localize("UTC")


def _bucket_probability(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "missing"
    if value < 0.55:
        return "<0.55"
    if value < 0.60:
        return "0.55-0.60"
    if value < 0.65:
        return "0.60-0.65"
    if value < 0.70:
        return "0.65-0.70"
    return ">=0.70"


def _classify_volatility(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "unknown"
    if value < 0.015:
        return "low"
    if value < 0.035:
        return "normal"
    return "high"


def _classify_trend(ret_12bar: float | None) -> str:
    if ret_12bar is None or pd.isna(ret_12bar):
        return "unknown"
    if ret_12bar > 0.02:
        return "bull"
    if ret_12bar < -0.02:
        return "bear"
    return "range"


def prepare_dataset_context(dataset: pd.DataFrame) -> pd.DataFrame:
    context = dataset.copy()
    context["timestamp"] = _to_utc_series(context["timestamp"])
    close = pd.to_numeric(context["close"], errors="coerce")
    ret_1 = close.pct_change()
    context["realized_volatility"] = ret_1.rolling(24, min_periods=6).std().shift(1)
    context["past_return_12bar"] = close.pct_change(12).shift(1)
    if "max_favorable_excursion_6bar" in context.columns:
        mfe = pd.to_numeric(context["max_favorable_excursion_6bar"], errors="coerce")
        context["mfe_proxy_pct"] = mfe.rolling(120, min_periods=20).mean().shift(1)
    else:
        context["mfe_proxy_pct"] = context["realized_volatility"] * 2.0
    context["volatility_regime"] = context["realized_volatility"].map(_classify_volatility)
    context["trend_regime"] = context["past_return_12bar"].map(_classify_trend)
    keep = [
        "timestamp",
        "realized_volatility",
        "mfe_proxy_pct",
        "volatility_regime",
        "trend_regime",
        "macro_regime",
        "derivatives_risk_regime",
        "combined_alpha_score",
        "alpha_score_v1_14",
        "ohlcv_only_alpha_score",
        "derivatives_regime_score",
    ]
    return context[[c for c in keep if c in context.columns]]


def build_signal_selection_features(
    *,
    signals_df: pd.DataFrame,
    dataset: pd.DataFrame,
    reconstructed: dict[str, dict[str, Any]],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Create one row per candidate/policy with realized outcomes and pre-trade features."""
    missing_fields: set[str] = set()
    rows: list[dict[str, Any]] = []
    signal_lookup = _signal_lookup(signals_df)
    context = prepare_dataset_context(dataset)

    for policy, bundle in reconstructed.items():
        candidates: list[TradeCandidate] = bundle.get("candidates", [])
        results: list[TradeSimulationResult] = bundle.get("results", [])
        candidate_lookup = {c.candidate_id: c for c in candidates}
        for result in results:
            cand = candidate_lookup.get(result.candidate_id)
            if cand is None:
                continue
            signal_meta = signal_lookup.get(_to_utc_timestamp(cand.signal_time))
            if signal_meta is None:
                missing_fields.add("signal_metadata")
                signal_meta = {}
            probability = _safe_float(signal_meta.get("predicted_probability", cand.confidence))
            cost_pct = _safe_float(result.cost_proxy_pct, DEFAULT_COST_PCT)
            diagnostic_forward_move = _diagnostic_forward_move_proxy(signal_meta)
            rows.append(
                {
                    "candidate_id": result.candidate_id,
                    "timestamp": _to_utc_timestamp(cand.signal_time),
                    "entry_time": _to_utc_timestamp(cand.entry_time),
                    "policy": policy,
                    "side": str(result.side),
                    "predicted_probability": probability,
                    "model_name": signal_meta.get("model_name", cand.source),
                    "target": signal_meta.get("target"),
                    "feature_set": signal_meta.get("feature_set"),
                    "split_name": signal_meta.get("split_name"),
                    "gross_pnl_pct": _safe_float(result.pnl_pct),
                    "net_pnl_pct": _safe_float(result.pnl_after_cost_pct),
                    "cost_pct": cost_pct,
                    "mfe_pct": _safe_float(result.mfe_pct),
                    "mae_pct": _safe_float(result.mae_pct),
                    "exit_reason": result.exit_reason,
                    "bars_held_intrabar": result.bars_held_intrabar,
                    "simulation_status": result.simulation_status,
                    "diagnostic_forward_move_pct": diagnostic_forward_move,
                }
            )

    features = pd.DataFrame(rows)
    if features.empty:
        return features, {"rows": 0, "missing_fields": sorted(missing_fields)}

    features["timestamp"] = _to_utc_series(features["timestamp"])
    features = features.merge(context, on="timestamp", how="left")
    if "realized_volatility" not in features:
        features["realized_volatility"] = np.nan
    if "mfe_proxy_pct" not in features:
        features["mfe_proxy_pct"] = np.nan

    fallback_move = (
        pd.to_numeric(features["realized_volatility"], errors="coerce").fillna(0.0) * 2.0
    )
    features["mfe_proxy_pct"] = pd.to_numeric(features["mfe_proxy_pct"], errors="coerce").fillna(
        fallback_move
    )
    features["causal_expected_move_pct"] = _causal_expected_move(features, fallback_move)
    # Backward-compatible name, now explicitly causal. The realized forward
    # return diagnostic is kept separate in diagnostic_forward_move_pct.
    features["gross_expected_move_pct"] = features["causal_expected_move_pct"]
    features["expected_move_model_pct"] = features["causal_expected_move_pct"]
    features["confidence_bucket"] = features["predicted_probability"].map(_bucket_probability)
    features["cost_to_expected_move_ratio"] = cost_to_move_ratio(
        features["gross_expected_move_pct"], features["cost_pct"]
    )
    features["gross_edge_after_cost"] = features["gross_expected_move_pct"] - features["cost_pct"]
    features["is_cost_viable"] = cost_viability_flags(
        features["gross_expected_move_pct"], features["cost_pct"], 1.0
    )
    features["is_high_confidence"] = pd.to_numeric(
        features["predicted_probability"], errors="coerce"
    ).fillna(0.0) >= 0.60
    features["is_high_volatility"] = features.get("volatility_regime", "unknown").eq("high")
    features["is_top_decile_by_probability"] = _top_quantile_flag(
        features, "predicted_probability", 0.90
    )
    features["is_top_decile_by_mfe_proxy"] = _top_quantile_flag(features, "mfe_proxy_pct", 0.90)
    missing = [
        column
        for column in ["predicted_probability", "realized_volatility", "mfe_proxy_pct"]
        if column not in features or features[column].isna().all()
    ]
    missing_fields.update(missing)
    forbidden_future_columns = _forbidden_future_columns_present(features)
    diagnostic_only_columns = [
        column for column in ["diagnostic_forward_move_pct"] if column in features.columns
    ]
    causal_feature_columns = [
        column
        for column in [
            "timestamp",
            "predicted_probability",
            "realized_volatility",
            "mfe_proxy_pct",
            "causal_expected_move_pct",
            "gross_expected_move_pct",
            "cost_pct",
            "volatility_regime",
            "trend_regime",
            "combined_alpha_score",
            "alpha_score_v1_14",
        ]
        if column in features.columns
    ]
    return features, {
        "rows": int(len(features)),
        "policies": sorted(features["policy"].dropna().unique().tolist()),
        "missing_fields": sorted(missing_fields),
        "forbidden_future_columns_present": forbidden_future_columns,
        "diagnostic_only_columns": diagnostic_only_columns,
        "causal_feature_columns": causal_feature_columns,
    }


def _signal_lookup(signals_df: pd.DataFrame) -> dict[pd.Timestamp, dict[str, Any]]:
    if signals_df.empty or "timestamp" not in signals_df:
        return {}
    temp = signals_df.copy()
    temp["timestamp"] = _to_utc_series(temp["timestamp"])
    return {
        pd.Timestamp(row["timestamp"]): row.to_dict()
        for _, row in temp.drop_duplicates("timestamp").iterrows()
    }


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _diagnostic_forward_move_proxy(signal_meta: dict[str, Any]) -> float:
    forward_6 = abs(_safe_float(signal_meta.get("forward_return_6bar"), 0.0))
    forward_12 = abs(_safe_float(signal_meta.get("forward_return_12bar"), 0.0))
    return max(forward_6, forward_12)


def _causal_expected_move(features: pd.DataFrame, fallback_move: pd.Series) -> pd.Series:
    probability = pd.to_numeric(features["predicted_probability"], errors="coerce").fillna(0.5)
    probability_edge = (probability - 0.5).clip(lower=0.0) * 2.0
    volatility_component = pd.to_numeric(
        features["realized_volatility"], errors="coerce"
    ).fillna(0.0) * 2.0
    mfe_component = pd.to_numeric(features["mfe_proxy_pct"], errors="coerce").fillna(0.0)
    base_move = pd.concat([volatility_component, mfe_component, fallback_move], axis=1).max(axis=1)
    alpha_column = "combined_alpha_score"
    if alpha_column not in features and "alpha_score_v1_14" in features:
        alpha_column = "alpha_score_v1_14"
    if alpha_column in features:
        alpha_strength = pd.to_numeric(features[alpha_column], errors="coerce").fillna(0.0).abs()
    else:
        alpha_strength = pd.Series(0.0, index=features.index)
    alpha_boost = (1.0 + alpha_strength.clip(upper=1.0) * 0.25).astype(float)
    causal_move = base_move * probability_edge * alpha_boost
    return causal_move.where(causal_move > 0, fallback_move).fillna(0.0)


def _forbidden_future_columns_present(features: pd.DataFrame) -> list[str]:
    prefixes = (
        "forward_return_",
        "max_favorable_excursion_",
        "max_adverse_excursion_",
    )
    exact = {
        "gross_pnl_pct",
        "net_pnl_pct",
        "mfe_pct",
        "mae_pct",
        "exit_reason",
        "simulation_status",
    }
    return sorted(
        column
        for column in features.columns
        if column in exact or any(column.startswith(prefix) for prefix in prefixes)
    )


def _top_quantile_flag(frame: pd.DataFrame, column: str, quantile: float) -> pd.Series:
    values = pd.to_numeric(frame[column], errors="coerce") if column in frame else pd.Series()
    if values.empty or values.dropna().empty:
        return pd.Series(False, index=frame.index)
    threshold = values.quantile(quantile)
    return values >= threshold
