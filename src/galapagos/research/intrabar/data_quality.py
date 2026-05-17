"""Data quality checks for intrabar data."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def audit_intrabar_quality(file_path: str, timeframe: str = "5min") -> dict[str, Any]:
    """Audit the quality of an intrabar parquet file."""
    if not Path(file_path).exists():
        return {"status": "error", "message": f"File not found: {file_path}"}
    
    df = pd.read_parquet(file_path)
    if df.empty:
        return {"status": "INTRABAR_DATA_TOO_SPARSE", "rows": 0}
    
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")
    
    # 1. Monotonicity
    is_monotonic = df["timestamp"].is_monotonic_increasing
    
    # 2. Duplicates
    duplicates = df.duplicated(subset=["timestamp"]).sum()
    
    # 3. Spacing (5m)
    expected_delta = pd.Timedelta(timeframe)
    diffs = df["timestamp"].diff().dropna()
    gaps = diffs[diffs != expected_delta]
    
    gap_info = []
    largest_gap = pd.Timedelta(0)
    largest_gap_start = None
    largest_gap_end = None
    
    if not gaps.empty:
        for idx, gap in gaps.items():
            if gap > largest_gap:
                largest_gap = gap
                largest_gap_start = df.loc[idx-1, "timestamp"]
                largest_gap_end = df.loc[idx, "timestamp"]
                
            gap_info.append({
                "after": df.loc[idx-1, "timestamp"].isoformat(),
                "before": df.loc[idx, "timestamp"].isoformat(),
                "gap": str(gap),
                "duration_seconds": gap.total_seconds()
            })
            if len(gap_info) > 20: break # Increased cap for V1.21.1
            
    # 4. OHLC Validity
    ohlc_valid = True
    bad_rows = df[
        (df["high"] < df["open"]) | 
        (df["high"] < df["close"]) | 
        (df["low"] > df["open"]) | 
        (df["low"] > df["close"]) |
        (df["high"] < df["low"]) |
        (df["volume"] < 0)
    ]
    if not bad_rows.empty:
        ohlc_valid = False
        
    time_range = df["timestamp"].max() - df["timestamp"].min()
    coverage_pct = 1.0
    if time_range.total_seconds() > 0:
        coverage_pct = (len(df) * expected_delta) / time_range
    
    status = "INTRABAR_DATA_QUALITY_OK"
    usable_for_continuous_backtest = True
    usable_for_gap_aware_signal_eval = True
    
    if not is_monotonic or duplicates > 0 or not ohlc_valid:
        status = "INTRABAR_DATA_INVALID"
        usable_for_continuous_backtest = False
        usable_for_gap_aware_signal_eval = False
    elif not gaps.empty:
        status = "INTRABAR_DATA_HAS_GAPS"
        usable_for_continuous_backtest = False
        # Still usable for signal eval if we handle gaps
        usable_for_gap_aware_signal_eval = True
        
    return {
        "status": status,
        "rows": len(df),
        "is_monotonic": bool(is_monotonic),
        "duplicates": int(duplicates),
        "ohlc_valid": bool(ohlc_valid),
        "gaps_count": len(gaps),
        "largest_gap_duration": str(largest_gap),
        "largest_gap_seconds": float(largest_gap.total_seconds()),
        "largest_gap_start": largest_gap_start.isoformat() if largest_gap_start else None,
        "largest_gap_end": largest_gap_end.isoformat() if largest_gap_end else None,
        "notable_gaps": gap_info,
        "coverage_pct": float(coverage_pct),
        "usable_for_continuous_backtest": usable_for_continuous_backtest,
        "usable_for_gap_aware_signal_eval": usable_for_gap_aware_signal_eval,
        "gap_aware_required": not gaps.empty,
        "start_time": df["timestamp"].min().isoformat(),
        "end_time": df["timestamp"].max().isoformat()
    }
