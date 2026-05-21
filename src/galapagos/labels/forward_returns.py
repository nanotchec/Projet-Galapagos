from __future__ import annotations

import numpy as np
import pandas as pd

from galapagos.labels.schemas import LABEL_COLUMNS_V2_6
from galapagos.labels.registry import HORIZONS, THRESHOLD, LABEL_SCHEMA_VERSION


def build_forward_labels(
    ohlcv_df: pd.DataFrame,
    source_ohlcv_sha256: str,
    label_run_id: str,
    *,
    label_schema_version: str = LABEL_SCHEMA_VERSION,
) -> pd.DataFrame:
    """Calculates forward looking labels for physical OHLCV series.
    
    Ensures a separate, non-overlapping label dataset with strict temporal metadata.
    """
    df = ohlcv_df.copy()
    
    close = df["close"].astype(float)
    close_ts = pd.to_datetime(df["close_ts"])
    
    # 1. Loop through horizons to calculate labels
    for h in HORIZONS:
        # Shift close prices backward (into the future)
        df[f"future_close_h{h}"] = close.shift(-h)
        
        # Calculate returns
        df[f"future_simple_return_h{h}"] = df[f"future_close_h{h}"] / close - 1.0
        df[f"future_log_return_h{h}"] = np.log(df[f"future_close_h{h}"] / close)
        
        # Calculate direction (1, -1, 0, or null)
        log_ret = df[f"future_log_return_h{h}"]
        df[f"direction_h{h}"] = np.where(
            log_ret.isna(),
            np.nan,
            np.where(log_ret > 0.0, 1.0, np.where(log_ret < 0.0, -1.0, 0.0))
        )
        
        # Calculate categorical up/down/flat label
        df[f"up_down_flat_h{h}"] = np.where(
            log_ret.isna(),
            None,
            np.where(log_ret > THRESHOLD, "UP", np.where(log_ret < -THRESHOLD, "DOWN", "FLAT"))
        )
        
        # Shift close_ts backward (into the future)
        # Using series shift to avoid timestamp type problems
        df[f"label_end_ts_h{h}"] = df["close_ts"].shift(-h)
        
        # Determine validity of horizon
        df[f"label_valid_h{h}"] = ~df[f"future_close_h{h}"].isna() & ~df[f"label_end_ts_h{h}"].isna()
        
    # 2. Compute label_available_ts (max of valid label_end_ts_h)
    # Since h1 < h3 < h5, if h5 is valid, label_available_ts is label_end_ts_h5.
    # If not, if h3 is valid, it is label_end_ts_h3.
    # If not, if h1 is valid, it is label_end_ts_h1.
    # Otherwise, it is None/NaN.
    df["label_available_ts"] = np.where(
        df["label_valid_h5"],
        df["label_end_ts_h5"],
        np.where(
            df["label_valid_h3"],
            df["label_end_ts_h3"],
            np.where(
                df["label_valid_h1"],
                df["label_end_ts_h1"],
                None
            )
        )
    )
    
    # Ensure correct datetime alignment or keep as string matching close_ts format
    # In V2.4/V2.5, timestamps are strings. Let's make sure available ts is handled consistently.
    df["label_available_ts"] = df["label_available_ts"].fillna(np.nan)
    
    # 3. Compute quality statistics
    # tail_row is True if any horizon is invalid
    df["tail_row"] = ~(df["label_valid_h1"] & df["label_valid_h3"] & df["label_valid_h5"])
    
    # Calculate counts of null values across label columns
    label_cols = []
    for h in HORIZONS:
        label_cols.extend([
            f"future_close_h{h}",
            f"future_log_return_h{h}",
            f"future_simple_return_h{h}",
            f"direction_h{h}",
            f"up_down_flat_h{h}",
            f"label_end_ts_h{h}",
        ])
    df["label_null_count"] = df[label_cols].isna().sum(axis=1).astype(int)
    df["label_error_count"] = 0
    
    # For invalid horizons, explicitly null out direction and classification
    for h in HORIZONS:
        invalid_mask = ~df[f"label_valid_h{h}"]
        df.loc[invalid_mask, f"direction_h{h}"] = np.nan
        df.loc[invalid_mask, f"up_down_flat_h{h}"] = None
        df.loc[invalid_mask, f"future_close_h{h}"] = np.nan
        df.loc[invalid_mask, f"future_simple_return_h{h}"] = np.nan
        df.loc[invalid_mask, f"future_log_return_h{h}"] = np.nan
        df.loc[invalid_mask, f"label_end_ts_h{h}"] = None
    
    # 4. Strict metadata alignment
    df["label_run_id"] = label_run_id
    df["source_ohlcv_sha256"] = source_ohlcv_sha256
    df["label_schema_version"] = label_schema_version
    
    # Types casting
    df["tail_row"] = df["tail_row"].astype(bool)
    for h in HORIZONS:
        df[f"label_valid_h{h}"] = df[f"label_valid_h{h}"].astype(bool)
        
    return df[LABEL_COLUMNS_V2_6].copy()
