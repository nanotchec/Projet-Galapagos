"""Feature set definitions for ML research — excludes all future/target columns."""
from __future__ import annotations

import pandas as pd

from galapagos.research.ml.targets import ALL_TARGET_COLUMNS

# Columns that must never be used as features
FORBIDDEN_FEATURE_PATTERNS = [
    "forward_return",
    "max_favorable_excursion",
    "max_adverse_excursion",
    "direction_up_after_cost",
    "tp_before_sl",
    "target_",
]
FORBIDDEN_EXACT = {
    "timestamp",
    "derivatives_available_timestamp",
    "available_timestamp",
    "derivatives_included",
    "macro_included",
    "derivatives_feature_status",
} | set(ALL_TARGET_COLUMNS)


def is_forbidden(column: str) -> bool:
    """Check if a column name is forbidden as a feature."""
    if column in FORBIDDEN_EXACT:
        return True
    return any(pattern in column for pattern in FORBIDDEN_FEATURE_PATTERNS)


def _safe_columns(dataset: pd.DataFrame, candidates: list[str]) -> list[str]:
    """Return columns that exist, are numeric, and are not forbidden."""
    result = []
    for col in candidates:
        if col not in dataset.columns or is_forbidden(col):
            continue
        if not pd.api.types.is_numeric_dtype(dataset[col]):
            continue
        result.append(col)
    return result


def build_ohlcv_basic_features(dataset: pd.DataFrame) -> pd.DataFrame:
    """Build OHLCV-derived features from raw price data."""
    frame = dataset.copy()
    close = pd.to_numeric(frame["close"], errors="coerce")
    high = pd.to_numeric(frame["high"], errors="coerce")
    low = pd.to_numeric(frame["low"], errors="coerce")
    volume = pd.to_numeric(frame["volume"], errors="coerce")

    # Lagged returns
    for lag in (1, 2, 3, 6, 12):
        frame[f"return_lag_{lag}"] = close.pct_change(lag, fill_method=None)

    # Realized volatility
    frame["realized_vol_12"] = close.pct_change(fill_method=None).rolling(12, min_periods=3).std()
    frame["realized_vol_42"] = close.pct_change(fill_method=None).rolling(42, min_periods=12).std()

    # ATR proxy
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs(),
    ], axis=1).max(axis=1)
    frame["atr_14"] = tr.rolling(14, min_periods=3).mean()
    frame["atr_42"] = tr.rolling(42, min_periods=12).mean()

    # Volume zscore
    vol_mean = volume.rolling(42, min_periods=12).mean()
    vol_std = volume.rolling(42, min_periods=12).std()
    frame["volume_zscore"] = ((volume - vol_mean) / vol_std.replace(0, pd.NA)).fillna(0.0)

    # Distance from high/low
    rolling_high = high.rolling(42, min_periods=12).max()
    rolling_low = low.rolling(42, min_periods=12).min()
    range_size = (rolling_high - rolling_low).replace(0, pd.NA)
    frame["dist_from_high_42"] = (rolling_high - close) / range_size
    frame["dist_from_low_42"] = (close - rolling_low) / range_size

    # Trend slope (linear regression slope proxy)
    frame["trend_slope_12"] = close.rolling(12, min_periods=3).apply(
        lambda x: (x.iloc[-1] - x.iloc[0]) / max(x.std(), 1e-8), raw=False
    )

    # Moving average distances
    for window in (12, 24, 72):
        ma = close.rolling(window, min_periods=max(3, window // 4)).mean()
        frame[f"dist_ma_{window}"] = (close - ma) / ma

    return frame


OHLCV_BASIC_COLUMNS = [
    "return_lag_1", "return_lag_2", "return_lag_3", "return_lag_6", "return_lag_12",
    "realized_vol_12", "realized_vol_42",
    "atr_14", "atr_42",
    "volume_zscore",
    "dist_from_high_42", "dist_from_low_42",
    "trend_slope_12",
    "dist_ma_12", "dist_ma_24", "dist_ma_72",
]

MACRO_COLUMNS = [
    "equity_market_trend", "liquidity_proxy", "vol_regime_vix",
    "term_spread", "credit_spread", "macro_confidence",
]

DERIVATIVES_COLUMNS = [
    "funding_rate_binance", "funding_rate_bybit",
    "long_short_ratio_binance", "open_interest_bybit",
    "premium_binance",
    "funding_rate_zscore", "open_interest_change_pct",
    "premium_zscore", "taker_volume_ratio",
]

ALPHA_SCORE_COLUMNS = [
    "combined_alpha_score", "ohlcv_momentum_score", "ohlcv_breakout_score",
    "volatility_quality_score", "macro_regime_score", "derivatives_regime_score",
    "cost_penalty_score", "crowded_trade_penalty", "missing_data_penalty",
    "combined_alpha_score_no_derivatives", "combined_alpha_score_no_macro",
    "ohlcv_only_alpha_score", "macro_derivatives_score",
]

FEATURE_SETS = {
    "ohlcv_basic": OHLCV_BASIC_COLUMNS,
    "ohlcv_macro": OHLCV_BASIC_COLUMNS + MACRO_COLUMNS,
    "ohlcv_derivatives": OHLCV_BASIC_COLUMNS + DERIVATIVES_COLUMNS,
    "ohlcv_macro_derivatives": OHLCV_BASIC_COLUMNS + MACRO_COLUMNS + DERIVATIVES_COLUMNS,
    "alpha_scores": ALPHA_SCORE_COLUMNS,
}


def get_feature_set(
    dataset: pd.DataFrame, name: str
) -> tuple[list[str], dict]:
    """Return (columns, report) for a named feature set."""
    if name not in FEATURE_SETS:
        raise ValueError(f"Unknown feature set: {name}. Known: {sorted(FEATURE_SETS)}")
    candidates = FEATURE_SETS[name]
    available = _safe_columns(dataset, candidates)
    missing = [c for c in candidates if c not in available]
    forbidden_found = [c for c in candidates if is_forbidden(c)]
    return available, {
        "feature_set": name,
        "requested": len(candidates),
        "available": len(available),
        "missing": missing,
        "forbidden_found": forbidden_found,
        "columns": available,
    }


def extract_features(
    dataset: pd.DataFrame, columns: list[str]
) -> pd.DataFrame:
    """Extract feature matrix, fill NaN with 0 for ML consumption."""
    return dataset[columns].fillna(0.0)
