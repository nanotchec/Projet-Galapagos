from __future__ import annotations

from typing import Any

import pandas as pd

FORWARD_RETURNS = [
    "forward_return_1bar",
    "forward_return_3bar",
    "forward_return_6bar",
    "forward_return_12bar",
]
SCORE_VARIANTS = [
    "combined_alpha_score",
    "combined_alpha_score_no_derivatives",
    "combined_alpha_score_no_macro",
    "ohlcv_only_alpha_score",
    "macro_derivatives_score",
    "derivatives_regime_score",
]


def analyze_alpha_score_quality(dataset: pd.DataFrame) -> dict[str, Any]:
    score = _numeric(dataset, "combined_alpha_score")
    payload = {
        "version": "V1.14",
        "rows": int(len(dataset)),
        "correlations": _correlations(dataset, "combined_alpha_score"),
        "bucket_analysis": _bucket_analysis(dataset, "combined_alpha_score"),
        "top_bucket_vs_random": _top_bucket_vs_random(dataset, "combined_alpha_score"),
        "by_regime": _by_regime(dataset, "combined_alpha_score"),
        "variants": {
            column: {
                "correlations": _correlations(dataset, column),
                "top_bucket": _top_bucket_vs_random(dataset, column),
            }
            for column in SCORE_VARIANTS
            if column in dataset.columns
        },
        "missing_rate": float(score.isna().mean()),
    }
    payload["verdict"] = _verdict(payload)
    return payload


def analyze_derivatives_contribution(dataset: pd.DataFrame) -> dict[str, Any]:
    variants = {
        "ohlcv_only": "ohlcv_only_alpha_score",
        "combined_without_derivatives": "combined_alpha_score_no_derivatives",
        "combined_with_derivatives": "combined_alpha_score",
        "derivatives_only": "derivatives_regime_score",
        "macro_plus_derivatives": "macro_derivatives_score",
    }
    results = {
        name: {
            "column": column,
            "correlations": _correlations(dataset, column),
            "top_bucket": _top_bucket_vs_random(dataset, column),
            "missing_rate": float(_numeric(dataset, column).isna().mean()),
        }
        for name, column in variants.items()
        if column in dataset.columns
    }
    payload = {
        "version": "V1.14",
        "rows": int(len(dataset)),
        "variants": results,
        "derivatives_missing_rate": _missing(dataset, "derivatives_regime_score"),
    }
    payload["verdict"] = _contribution_verdict(payload)
    return payload


def _correlations(dataset: pd.DataFrame, score_column: str) -> dict[str, float | None]:
    if score_column not in dataset.columns:
        return {}
    score = _numeric(dataset, score_column)
    results: dict[str, float | None] = {}
    for column in FORWARD_RETURNS:
        if column not in dataset.columns:
            results[column] = None
            continue
        joined = pd.concat([score, _numeric(dataset, column)], axis=1).dropna()
        results[column] = (
            None if len(joined) < 3 else float(joined.iloc[:, 0].corr(joined.iloc[:, 1]))
        )
    return results


def _bucket_analysis(dataset: pd.DataFrame, score_column: str) -> dict[str, dict[str, Any]]:
    if score_column not in dataset.columns or dataset.empty:
        return {}
    scores = _numeric(dataset, score_column)
    try:
        buckets = pd.qcut(scores.rank(method="first"), 5, labels=[
            "bottom_20",
            "20_40",
            "40_60",
            "60_80",
            "top_20",
        ])
    except ValueError:
        return {}
    return {
        str(label): _summary(dataset[buckets == label])
        for label in buckets.dropna().unique()
    }


def _top_bucket_vs_random(dataset: pd.DataFrame, score_column: str) -> dict[str, Any]:
    buckets = _bucket_analysis(dataset, score_column)
    top = buckets.get("top_20", {})
    all_summary = _summary(dataset)
    return {
        "top_count": top.get("count", 0),
        "top_mean_forward_return_6bar": top.get("mean_forward_return_6bar"),
        "all_mean_forward_return_6bar": all_summary.get("mean_forward_return_6bar"),
        "beats_all_proxy": (
            None
            if top.get("mean_forward_return_6bar") is None
            else top.get("mean_forward_return_6bar", 0)
            > (all_summary.get("mean_forward_return_6bar") or 0)
        ),
        "warning": "random proxy only; not a proof of edge",
    }


def _by_regime(dataset: pd.DataFrame, score_column: str) -> dict[str, Any]:
    for column in ["market_regime", "regime_label", "macro_regime", "derivatives_risk_regime"]:
        if column in dataset.columns:
            return {
                str(regime): _summary(group)
                for regime, group in dataset.groupby(column, dropna=True)
            }
    return {}


def _summary(frame: pd.DataFrame) -> dict[str, Any]:
    output: dict[str, Any] = {"count": int(len(frame))}
    for column in FORWARD_RETURNS:
        output[f"mean_{column}"] = _mean(frame, column)
    output["hit_rate_after_cost_6bar"] = _hit_rate(frame, "forward_return_6bar", threshold=0.003)
    output["mean_mfe_6bar"] = _mean(frame, "max_favorable_excursion_6bar")
    output["mean_mae_6bar"] = _mean(frame, "max_adverse_excursion_6bar")
    output["warning"] = (
        "sample_lt_30"
        if len(frame) < 30
        else ("sample_lt_100" if len(frame) < 100 else None)
    )
    return output


def _verdict(payload: dict[str, Any]) -> str:
    corr = payload.get("correlations", {}).get("forward_return_6bar")
    top = payload.get("top_bucket_vs_random", {})
    count = top.get("top_count") or 0
    if count < 100:
        return "ALPHA_SCORE_NEED_MORE_DATA"
    if corr is None or abs(corr) < 0.02:
        return "ALPHA_SCORE_NO_EDGE"
    if top.get("beats_all_proxy") and corr > 0:
        return "ALPHA_SCORE_WEAK_EDGE_BEFORE_COSTS"
    return "ALPHA_SCORE_NEEDS_REWEIGHTING"


def _contribution_verdict(payload: dict[str, Any]) -> str:
    variants = payload.get("variants", {})
    with_der = variants.get("combined_with_derivatives", {}).get("top_bucket", {})
    without = variants.get("combined_without_derivatives", {}).get("top_bucket", {})
    if (
        payload.get("derivatives_missing_rate") is not None
        and payload["derivatives_missing_rate"] > 0.8
    ):
        return "DERIVATIVES_TOO_SPARSE_TO_EVALUATE"
    with_value = with_der.get("top_mean_forward_return_6bar")
    without_value = without.get("top_mean_forward_return_6bar")
    if with_value is None or without_value is None:
        return "DERIVATIVES_TOO_SPARSE_TO_EVALUATE"
    derivative_corr = (
        variants.get("derivatives_only", {})
        .get("correlations", {})
        .get("forward_return_6bar")
    )
    if derivative_corr is None or abs(derivative_corr) < 0.02:
        return "DERIVATIVES_CONTRIBUTION_WEAK"
    if with_value > without_value:
        return "DERIVATIVES_CONTRIBUTE_POSITIVELY"
    if with_value < without_value:
        return "DERIVATIVES_CONTRIBUTION_NEGATIVE"
    return "DERIVATIVES_CONTRIBUTION_WEAK"


def _numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(pd.NA, index=frame.index, dtype="Float64")
    return pd.to_numeric(frame[column], errors="coerce")


def _mean(frame: pd.DataFrame, column: str) -> float | None:
    if column not in frame.columns or frame.empty:
        return None
    value = _numeric(frame, column).mean()
    return None if pd.isna(value) else float(value)


def _hit_rate(frame: pd.DataFrame, column: str, threshold: float = 0.0) -> float | None:
    if column not in frame.columns or frame.empty:
        return None
    values = _numeric(frame, column).dropna()
    return None if values.empty else float((values > threshold).mean())


def _missing(frame: pd.DataFrame, column: str) -> float | None:
    return None if column not in frame.columns else float(frame[column].isna().mean())
