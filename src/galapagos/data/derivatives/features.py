from __future__ import annotations

import pandas as pd


def causal_zscore(series: pd.Series, window: int = 30) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    shifted = values.shift(1)
    mean = shifted.rolling(window, min_periods=max(3, window // 3)).mean()
    std = shifted.rolling(window, min_periods=max(3, window // 3)).std()
    return (values - mean) / std.replace(0, pd.NA)


def build_derivatives_features(records: pd.DataFrame, timeframe: str = "4h") -> pd.DataFrame:
    if records.empty:
        return pd.DataFrame(
            columns=["timestamp", "available_timestamp", "feature_status", "timeframe"]
        )
    records = records.copy()
    records["available_timestamp"] = pd.to_datetime(
        records["available_timestamp"],
        utc=True,
        errors="coerce",
        format="mixed",
    )
    records["source_metric"] = (
        records["metric_name"].astype(str) + "_" + records["source"].astype(str)
    )
    by_source = records.pivot_table(
        index="available_timestamp",
        columns="source_metric",
        values="metric_value",
        aggfunc="last",
    ).sort_index()
    generic = records.pivot_table(
        index="available_timestamp",
        columns="metric_name",
        values="metric_value",
        aggfunc="mean",
    ).sort_index()
    pivot = by_source.join(generic, how="outer").sort_index()
    output = pivot.reset_index().sort_values("available_timestamp")
    output["timestamp"] = pd.to_datetime(output["available_timestamp"], utc=True, format="mixed")
    output["timeframe"] = timeframe
    output["feature_status"] = "available"
    _rename_if_present(output, "funding_rate_binance", "funding_rate_binance")
    _rename_if_present(output, "funding_rate_bybit", "funding_rate_bybit")
    _rename_if_present(output, "open_interest_binance", "open_interest_binance")
    _rename_if_present(output, "open_interest_bybit", "open_interest_bybit")
    _rename_if_present(output, "premium_binance", "premium_binance")
    _rename_if_present(output, "premium_bybit", "premium_bybit")
    output["funding_rate_mean"] = _mean_existing(
        output,
        ["funding_rate_binance", "funding_rate_bybit", "funding_rate"],
    )
    output["funding_rate_spread_binance_bybit"] = _diff_existing(
        output,
        "funding_rate_binance",
        "funding_rate_bybit",
    )
    output["funding_rate_diff_binance_bybit"] = _diff_existing(
        output,
        "funding_rate_binance",
        "funding_rate_bybit",
    )
    output["funding_rate_zscore_30d"] = causal_zscore(output["funding_rate_mean"], window=180)
    output["funding_rate_zscore_90d"] = causal_zscore(output["funding_rate_mean"], window=540)
    output["funding_rate_change_1"] = output["funding_rate_mean"].astype(float).diff()
    output["funding_rate_change_3"] = output["funding_rate_mean"].astype(float).diff(3)
    output["funding_zscore_30d"] = output["funding_rate_zscore_30d"]
    output["funding_zscore_90d"] = output["funding_rate_zscore_90d"]
    output["funding_trend_3"] = output["funding_rate_change_3"]
    output["funding_extreme_positive"] = output["funding_rate_zscore_30d"] >= 2
    output["funding_extreme_negative"] = output["funding_rate_zscore_30d"] <= -2

    output["open_interest_mean"] = _mean_existing(
        output,
        ["open_interest_binance", "open_interest_bybit", "open_interest"],
    )
    output["open_interest_change_1"] = output["open_interest_mean"].astype(float).pct_change(
        fill_method=None
    )
    output["open_interest_change_3"] = output["open_interest_mean"].astype(float).pct_change(
        3,
        fill_method=None,
    )
    output["open_interest_zscore_30d"] = causal_zscore(output["open_interest_mean"], window=180)
    output["open_interest_zscore_90d"] = causal_zscore(output["open_interest_mean"], window=540)
    output["oi_change_1"] = output["open_interest_change_1"]
    output["oi_change_3"] = output["open_interest_change_3"]
    output["oi_zscore_30d"] = output["open_interest_zscore_30d"]
    output["oi_zscore_90d"] = output["open_interest_zscore_90d"]

    output["premium_mean"] = _mean_existing(output, ["premium_binance", "premium_bybit", "premium"])
    output["premium_zscore_30d"] = causal_zscore(output["premium_mean"], window=180)
    output["basis_proxy"] = output["premium_mean"]
    output["premium_proxy"] = output["premium_mean"]

    if "long_short_ratio" in output.columns:
        output["long_short_ratio_zscore"] = causal_zscore(output["long_short_ratio"], window=180)
    if {"taker_buy_volume", "taker_sell_volume"}.issubset(output.columns):
        denominator = output["taker_sell_volume"].replace(0, pd.NA)
        output["taker_buy_sell_ratio"] = output["taker_buy_volume"] / denominator
        total = output["taker_buy_volume"] + output["taker_sell_volume"]
        output["taker_imbalance"] = (
            output["taker_buy_volume"] - output["taker_sell_volume"]
        ) / total.replace(0, pd.NA)
    elif "taker_buy_sell_ratio" in output.columns:
        ratio = output["taker_buy_sell_ratio"].astype(float)
        output["taker_imbalance"] = (ratio - 1.0) / (ratio + 1.0).replace(0, pd.NA)
    else:
        output["taker_buy_sell_ratio"] = pd.NA
        output["taker_imbalance"] = pd.NA
    output["taker_imbalance_zscore"] = causal_zscore(output["taker_imbalance"], window=180)
    output["long_short_crowding"] = (
        output["long_short_ratio_zscore"].abs()
        if "long_short_ratio_zscore" in output.columns
        else pd.Series(pd.NA, index=output.index, dtype="Float64")
    )
    output["price_oi_divergence"] = -output["open_interest_change_1"]
    output["price_oi_confirmation"] = output["open_interest_change_1"].where(
        output["open_interest_change_1"] > 0,
        0,
    )
    output["liquidation_proxy"] = pd.NA
    available_cols = [
        "funding_rate_mean",
        "open_interest_mean",
        "premium_mean",
        "taker_buy_sell_ratio",
        "long_short_ratio",
    ]
    output["derivatives_available_count"] = output[
        [col for col in available_cols if col in output.columns]
    ].notna().sum(axis=1)
    output["derivatives_missing_count"] = (
        len(available_cols) - output["derivatives_available_count"]
    )
    output["derivatives_confidence_score"] = (
        output["derivatives_available_count"] / len(available_cols)
    )
    output["derivatives_risk_regime"] = output.apply(_risk_regime, axis=1)
    output["derivatives_crowding_score"] = (
        _bounded_abs(output.get("long_short_ratio_zscore"))
        if "long_short_ratio_zscore" in output.columns
        else pd.Series(pd.NA, index=output.index, dtype="Float64")
    )
    output["derivatives_leverage_score"] = _bounded(
        output["open_interest_change_3"].astype(float).fillna(0) * 10
    )
    output["derivatives_regime_score"] = output.apply(_regime_score, axis=1)
    output["derivatives_score"] = output["derivatives_regime_score"] - (
        output["derivatives_missing_count"] / len(available_cols) * 0.25
    )
    return output


def _rename_if_present(frame: pd.DataFrame, old: str, new: str) -> None:
    if old in frame.columns and old != new:
        frame.rename(columns={old: new}, inplace=True)


def _mean_existing(frame: pd.DataFrame, columns: list[str]) -> pd.Series:
    existing = [column for column in columns if column in frame.columns]
    if not existing:
        return pd.Series(pd.NA, index=frame.index, dtype="Float64")
    return frame[existing].astype(float).mean(axis=1)


def _diff_existing(frame: pd.DataFrame, left: str, right: str) -> pd.Series:
    if {left, right}.issubset(frame.columns):
        return frame[left].astype(float) - frame[right].astype(float)
    return pd.Series(pd.NA, index=frame.index, dtype="Float64")


def _risk_regime(row: pd.Series) -> str:
    funding_z = row.get("funding_rate_zscore_30d")
    oi_change = row.get("open_interest_change_3")
    long_short_z = row.get("long_short_ratio_zscore")
    if pd.notna(funding_z) and funding_z >= 2:
        return "positive_funding_extreme"
    if pd.notna(funding_z) and funding_z <= -2:
        return "negative_funding_extreme"
    if pd.notna(long_short_z) and long_short_z >= 2:
        return "crowded_long"
    if pd.notna(long_short_z) and long_short_z <= -2:
        return "crowded_short"
    if pd.notna(oi_change) and oi_change > 0.05:
        return "leverage_expanding"
    if pd.notna(oi_change) and oi_change < -0.05:
        return "leverage_contracting"
    if row.get("derivatives_available_count", 0) == 0:
        return "unknown"
    return "neutral"


def _bounded(series: pd.Series | None) -> pd.Series:
    if series is None:
        return pd.Series(dtype="Float64")
    return pd.to_numeric(series, errors="coerce").clip(-1, 1)


def _bounded_abs(series: pd.Series | None) -> pd.Series:
    if series is None:
        return pd.Series(dtype="Float64")
    return pd.to_numeric(series, errors="coerce").abs().clip(0, 3) / 3


def _regime_score(row: pd.Series) -> float:
    score = 0.0
    funding_z = row.get("funding_rate_zscore_30d")
    oi_change = row.get("open_interest_change_3")
    premium_z = row.get("premium_zscore_30d")
    taker_z = row.get("taker_imbalance_zscore")
    if pd.notna(funding_z):
        score -= min(abs(float(funding_z)) / 3, 1.0) * 0.35
    if pd.notna(oi_change):
        score += max(min(float(oi_change) * 10, 0.4), -0.4)
    if pd.notna(premium_z):
        score -= min(abs(float(premium_z)) / 3, 1.0) * 0.2
    if pd.notna(taker_z):
        score += max(min(float(taker_z) / 3, 0.25), -0.25)
    score += float(row.get("derivatives_confidence_score", 0) or 0) * 0.2
    return max(min(score, 1.0), -1.0)
