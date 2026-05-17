"""Logic for analyzing signal coverage relative to intrabar data gaps."""
from __future__ import annotations

from typing import Any

import pandas as pd


def analyze_signal_gap_impact(
    signals_df: pd.DataFrame,
    intrabar_df: pd.DataFrame,
    timeframe: str = "5min"
) -> dict[str, Any]:
    """
    Analyze which signals fall into gaps or covered segments.
    Distinguishes between raw prediction rows and unique signal timestamps.
    """
    if signals_df.empty or intrabar_df.empty:
        return {"status": "error", "message": "Empty signals or intrabar data"}

    # Use copies to avoid modifying original df
    signals_df = signals_df.copy()
    intrabar_df = intrabar_df.copy()

    signals_df["timestamp"] = pd.to_datetime(signals_df["timestamp"], utc=True)
    intrabar_df["timestamp"] = pd.to_datetime(intrabar_df["timestamp"], utc=True)
    
    # 1. Identify covered segments
    intrabar_df = intrabar_df.sort_values("timestamp")
    expected_delta = pd.Timedelta(timeframe)
    diffs = intrabar_df["timestamp"].diff()
    
    # Indices where a new segment starts (gap before it)
    # First row always starts a segment
    segment_starts = intrabar_df.index[diffs > expected_delta].tolist()
    segment_starts = [intrabar_df.index[0]] + segment_starts
    
    segments = []
    for i in range(len(segment_starts)):
        start_idx = segment_starts[i]
        if i + 1 < len(segment_starts):
            # The row before the next segment starts is the end of the current segment
            # We use positional indexing to find the actual end row in the sorted df
            end_pos = intrabar_df.index.get_loc(segment_starts[i+1]) - 1
            end_idx = intrabar_df.index[end_pos]
        else:
            end_idx = intrabar_df.index[-1]
            
        segments.append({
            "start": intrabar_df.loc[start_idx, "timestamp"],
            "end": intrabar_df.loc[end_idx, "timestamp"]
        })

    # 2. Map signals to segments or gaps
    def check_signal(ts):
        for s in segments:
            if s["start"] <= ts <= s["end"]:
                return "covered"
        return "gap"

    # Analyze raw rows
    signals_df["coverage_status"] = signals_df["timestamp"].apply(check_signal)
    raw_stats = signals_df["coverage_status"].value_counts().to_dict()
    raw_total = len(signals_df)
    raw_gap = raw_stats.get("gap", 0)
    raw_gap_ratio = raw_gap / raw_total if raw_total > 0 and raw_gap > 0 else 0.0

    # Analyze unique timestamps
    unique_ts_df = signals_df.drop_duplicates("timestamp").copy()
    unique_total = len(unique_ts_df)
    unique_gap = unique_ts_df["coverage_status"].value_counts().get("gap", 0)
    unique_gap_ratio = unique_gap / unique_total if unique_total > 0 and unique_gap > 0 else 0.0
    
    # Identify largest gap duration
    gaps_only = diffs[diffs > expected_delta]
    largest_gap_duration = gaps_only.max() if not gaps_only.empty else pd.Timedelta(0)

    # Verdict logic
    verdict = "GAP_IMPACT_LIMITED"
    if unique_gap_ratio > 0.05:
        verdict = "GAP_IMPACT_SIGNIFICANT"
    
    if unique_gap > 0:
        verdict += "_GAP_AWARE_EVALUATION_REQUIRED"
        
    if unique_gap_ratio > 0.20:
        verdict += "_GAP_FILL_REQUIRED_BEFORE_STRONG_COMPARISON"

    return {
        "total_signals": raw_total,
        "covered_signals": int(raw_total - raw_gap),
        "signals_in_gap": int(raw_gap),
        "gap_signals": int(raw_gap),
        "signals_gap_ratio": float(raw_gap_ratio),
        "raw_prediction_rows_total": raw_total,
        "raw_prediction_rows_in_gap": int(raw_gap),
        "raw_prediction_rows_gap_ratio": float(raw_gap_ratio),
        
        "unique_signal_timestamps_total": unique_total,
        "unique_signal_timestamps_in_gap": int(unique_gap),
        "unique_signal_timestamps_gap_ratio": float(unique_gap_ratio),
        
        "trade_candidates_total": None, # Filled by script if candidates loaded
        "trade_candidates_in_gap": None,
        "trade_candidates_gap_ratio": None,
        
        "segments_count": len(segments),
        "largest_gap_duration": str(largest_gap_duration),
        "verdict": verdict,
        "is_biased_by_missing_segment": unique_gap_ratio > 0.10
    }
