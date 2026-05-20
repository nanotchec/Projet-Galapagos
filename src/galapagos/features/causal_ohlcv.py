from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Any
from pathlib import Path

from galapagos.features.schemas import FEATURE_COLUMNS_V2_5


def build_causal_features(
    ohlcv_df: pd.DataFrame,
    source_ohlcv_sha256: str,
    feature_run_id: str,
    *,
    feature_schema_version: str = "V2.5",
) -> pd.DataFrame:
    """Calculates causal OHLCV features from validated OHLCV data.
    
    Ensures all calculations are causal (past & present observations only).
    """
    df = ohlcv_df.copy()
    
    # Extract inputs for readability
    close = df["close"].astype(float)
    open_ = df["open"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    volume = df["volume"].astype(float)
    
    # 1. Price / past returns
    df["close_lag_1"] = close.shift(1)
    df["return_1"] = close / df["close_lag_1"] - 1.0
    # Safe log return calculation to prevent negative/null division issues
    df["log_return_1"] = np.log(close / df["close_lag_1"])
    
    df["return_3"] = close / close.shift(3) - 1.0
    df["log_return_3"] = np.log(close / close.shift(3))
    
    df["return_5"] = close / close.shift(5) - 1.0
    df["log_return_5"] = np.log(close / close.shift(5))
    
    # 2. Past volatility
    df["rolling_vol_5"] = df["log_return_1"].rolling(5, min_periods=5).std()
    df["rolling_vol_15"] = df["log_return_1"].rolling(15, min_periods=15).std()
    df["rolling_vol_30"] = df["log_return_1"].rolling(30, min_periods=30).std()
    
    # 3. Candle range / structure
    df["candle_range"] = high - low
    df["candle_body"] = np.abs(close - open_)
    df["upper_wick"] = high - np.maximum(open_, close)
    df["lower_wick"] = np.minimum(open_, close) - low
    
    # Close position in range: (close - low) / (high - low) with division-by-zero guard
    denom_range = high - low
    df["close_position_in_range"] = np.where(
        denom_range > 0.0,
        (close - low) / denom_range,
        0.0
    )
    
    # 4. Volume features
    df["volume_lag_1"] = volume.shift(1)
    # volume_return_1 with division-by-zero guard
    vol_lag = df["volume_lag_1"]
    df["volume_return_1"] = np.where(
        vol_lag > 0.0,
        (volume - vol_lag) / vol_lag,
        0.0
    )
    
    df["rolling_volume_mean_5"] = volume.rolling(5, min_periods=5).mean()
    df["rolling_volume_mean_15"] = volume.rolling(15, min_periods=15).mean()
    
    # rolling_volume_zscore_15 with standard deviation == 0 guard
    rolling_vol_std_15 = volume.rolling(15, min_periods=15).std()
    df["rolling_volume_zscore_15"] = np.where(
        rolling_vol_std_15 > 0.0,
        (volume - df["rolling_volume_mean_15"]) / rolling_vol_std_15,
        0.0
    )
    
    # 5. Trend / distance
    df["sma_5"] = close.rolling(5, min_periods=5).mean()
    df["sma_15"] = close.rolling(15, min_periods=15).mean()
    df["sma_30"] = close.rolling(30, min_periods=30).mean()
    
    df["close_to_sma_5"] = close / df["sma_5"] - 1.0
    df["close_to_sma_15"] = close / df["sma_15"] - 1.0
    df["close_to_sma_30"] = close / df["sma_30"] - 1.0
    
    # 6. Temporal features
    event_dt = pd.to_datetime(df["event_ts"], utc=True)
    df["hour_utc"] = event_dt.dt.hour.astype(int)
    df["day_of_week_utc"] = event_dt.dt.dayofweek.astype(int)
    df["is_weekend_utc"] = df["day_of_week_utc"].isin([5, 6]).astype(bool)
    
    # 7. Warmup and quality features
    # Numeric features calculated with rolling windows or lags
    warmup_cols = [
        "close_lag_1", "return_1", "log_return_1", "return_3", "log_return_3",
        "return_5", "log_return_5", "rolling_vol_5", "rolling_vol_15", "rolling_vol_30",
        "volume_lag_1", "volume_return_1", "rolling_volume_mean_5", "rolling_volume_mean_15",
        "rolling_volume_zscore_15", "sma_5", "sma_15", "sma_30", "close_to_sma_5",
        "close_to_sma_15", "close_to_sma_30"
    ]
    df["warmup_row"] = df[warmup_cols].isna().any(axis=1).astype(bool)
    
    # Count of NaN values on calculated numerical features
    numeric_feature_cols = warmup_cols + [
        "candle_range", "candle_body", "upper_wick", "lower_wick", "close_position_in_range"
    ]
    df["feature_null_count"] = df[numeric_feature_cols].isna().sum(axis=1).astype(int)
    df["feature_error_count"] = 0
    
    # 8. Causal metadata alignment
    df["feature_available_ts"] = df["available_ts"]
    df["decision_ts"] = df["available_ts"]
    df["feature_run_id"] = feature_run_id
    df["source_ohlcv_sha256"] = source_ohlcv_sha256
    df["feature_schema_version"] = feature_schema_version
    
    # Cast boolean columns explicitly
    df["warmup_row"] = df["warmup_row"].astype(bool)
    df["is_weekend_utc"] = df["is_weekend_utc"].astype(bool)
    
    # 9. strict schema ordering
    return df[FEATURE_COLUMNS_V2_5].copy()
