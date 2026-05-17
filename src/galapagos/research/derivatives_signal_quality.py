from __future__ import annotations

from typing import Any

import pandas as pd

FORWARD_COLUMNS = [
    "forward_return_1bar",
    "forward_return_3bar",
    "forward_return_6bar",
    "forward_return_12bar",
]


def analyze_derivatives_signal_quality(dataset: pd.DataFrame) -> dict[str, Any]:
    groups = {
        "funding_positive_extreme": _mask(dataset, "funding_rate_zscore_30d", lower=2),
        "funding_negative_extreme": _mask(dataset, "funding_rate_zscore_30d", upper=-2),
        "oi_expanding": _mask(dataset, "open_interest_change_3", lower=0.05),
        "oi_contracting": _mask(dataset, "open_interest_change_3", upper=-0.05),
        "premium_positive_extreme": _mask(dataset, "premium_zscore_30d", lower=2),
        "premium_negative_extreme": _mask(dataset, "premium_zscore_30d", upper=-2),
        "taker_buy_dominance": _mask(dataset, "taker_imbalance", lower=0.2),
        "taker_sell_dominance": _mask(dataset, "taker_imbalance", upper=-0.2),
    }
    if "derivatives_risk_regime" in dataset.columns:
        for regime in sorted(dataset["derivatives_risk_regime"].dropna().unique()):
            groups[f"regime_{regime}"] = dataset["derivatives_risk_regime"] == regime
    results = {
        name: summarize_group(dataset[mask])
        for name, mask in groups.items()
        if isinstance(mask, pd.Series)
    }
    verdicts = _verdicts(results, dataset)
    return {
        "version": "V1.14",
        "groups": results,
        "verdicts": verdicts,
        "sample_warning": "warning if sample < 30 / low confidence if sample < 100",
    }


def summarize_group(frame: pd.DataFrame) -> dict[str, Any]:
    summary: dict[str, Any] = {"count": int(len(frame))}
    for column in FORWARD_COLUMNS:
        summary[f"mean_{column}"] = _mean(frame, column)
    summary["median_forward_return_6bar"] = _median(frame, "forward_return_6bar")
    summary["hit_rate_6bar"] = _hit_rate(frame, "forward_return_6bar")
    summary["mean_mfe_6bar"] = _mean(frame, "max_favorable_excursion_6bar")
    summary["mean_mae_6bar"] = _mean(frame, "max_adverse_excursion_6bar")
    summary["cost_adjusted_forward_return_6bar"] = (
        None if summary["mean_forward_return_6bar"] is None
        else summary["mean_forward_return_6bar"] - 0.003
    )
    summary["warning"] = (
        "sample_lt_30"
        if len(frame) < 30
        else ("sample_lt_100" if len(frame) < 100 else None)
    )
    return summary


def compare_with_without_derivatives(dataset: pd.DataFrame) -> dict[str, Any]:
    base = summarize_group(dataset)
    derivative_known = dataset[
        dataset.get("derivatives_available_count", pd.Series(0, index=dataset.index)).fillna(0) > 0
    ]
    derivative_high_conf = dataset[
        dataset.get("derivatives_confidence_score", pd.Series(0, index=dataset.index)).fillna(0)
        >= 0.4
    ]
    payload = {
        "version": "V1.14",
        "ohlcv_only_proxy": base,
        "with_derivatives_available": summarize_group(derivative_known),
        "with_derivatives_high_confidence": summarize_group(derivative_high_conf),
        "missing_rate_derivatives_available_count": _missing(
            dataset,
            "derivatives_available_count",
        ),
    }
    payload["verdict"] = _comparison_verdict(payload)
    return payload


def analyze_filter_hypotheses(dataset: pd.DataFrame) -> dict[str, Any]:
    filters = {
        "avoid_positive_funding_extreme": ~_mask(dataset, "funding_rate_zscore_30d", lower=2),
        "avoid_negative_funding_extreme": ~_mask(dataset, "funding_rate_zscore_30d", upper=-2),
        "avoid_premium_extreme": ~(
            _mask(dataset, "premium_zscore_30d", lower=2)
            | _mask(dataset, "premium_zscore_30d", upper=-2)
        ),
        "avoid_low_derivatives_confidence": dataset.get(
            "derivatives_confidence_score",
            pd.Series(0, index=dataset.index),
        ).fillna(0) >= 0.4,
        "avoid_crowded_regimes": ~dataset.get(
            "derivatives_risk_regime",
            pd.Series("unknown", index=dataset.index),
        ).isin(["crowded_long", "crowded_short", "positive_funding_extreme"]),
    }
    results = {name: summarize_group(dataset[mask]) for name, mask in filters.items()}
    return {
        "version": "V1.14",
        "filters": results,
        "verdict": _filter_verdict(results),
        "warning": "Hypotheses offline uniquement; aucune regle trading modifiee.",
    }


def _mask(
    frame: pd.DataFrame,
    column: str,
    *,
    lower: float | None = None,
    upper: float | None = None,
) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(False, index=frame.index)
    values = pd.to_numeric(frame[column], errors="coerce")
    if lower is not None:
        return values >= lower
    if upper is not None:
        return values <= upper
    return values.notna()


def _mean(frame: pd.DataFrame, column: str) -> float | None:
    if column not in frame.columns or frame.empty:
        return None
    value = pd.to_numeric(frame[column], errors="coerce").mean()
    return None if pd.isna(value) else float(value)


def _median(frame: pd.DataFrame, column: str) -> float | None:
    if column not in frame.columns or frame.empty:
        return None
    value = pd.to_numeric(frame[column], errors="coerce").median()
    return None if pd.isna(value) else float(value)


def _hit_rate(frame: pd.DataFrame, column: str) -> float | None:
    if column not in frame.columns or frame.empty:
        return None
    values = pd.to_numeric(frame[column], errors="coerce").dropna()
    return None if values.empty else float((values > 0).mean())


def _missing(frame: pd.DataFrame, column: str) -> float | None:
    return None if column not in frame.columns else float(frame[column].isna().mean())


def _verdicts(results: dict[str, dict[str, Any]], dataset: pd.DataFrame) -> list[str]:
    if not any(name.startswith(("funding", "oi", "premium", "taker")) for name in results):
        return ["DERIVATIVES_DATA_TOO_SPARSE"]
    available_count = dataset.get(
        "derivatives_available_count",
        pd.Series(0, index=dataset.index),
    )
    if available_count.fillna(0).sum() < 100:
        return ["DERIVATIVES_NEED_MORE_HISTORY"]
    candidates = [
        name for name, stats in results.items()
        if (stats.get("count") or 0) >= 100
        and (stats.get("cost_adjusted_forward_return_6bar") or -1) > 0
    ]
    if candidates:
        return ["DERIVATIVES_REGIME_FILTER_CANDIDATE"]
    return ["DERIVATIVES_NO_EDGE"]


def _comparison_verdict(payload: dict[str, Any]) -> str:
    base = payload["ohlcv_only_proxy"].get("mean_forward_return_6bar") or 0
    high = payload["with_derivatives_high_confidence"].get("mean_forward_return_6bar") or 0
    count = payload["with_derivatives_high_confidence"].get("count") or 0
    if count < 100:
        return "DERIVATIVES_TOO_SPARSE"
    if high > base:
        return "DERIVATIVES_IMPROVE_DISCRIMINATION"
    return "DERIVATIVES_DO_NOT_HELP"


def _filter_verdict(results: dict[str, dict[str, Any]]) -> str:
    viable = [
        stats for stats in results.values()
        if (stats.get("count") or 0) >= 100
        and (stats.get("cost_adjusted_forward_return_6bar") or -1) > 0
    ]
    return "DERIVATIVES_REGIME_FILTER_CANDIDATE" if viable else "DERIVATIVES_NO_EDGE"
