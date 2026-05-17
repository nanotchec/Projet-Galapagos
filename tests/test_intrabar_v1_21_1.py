"""Tests for Galapagos V1.21.1 Gap-Aware logic."""
from __future__ import annotations

import pandas as pd

from galapagos.research.intrabar.data_quality import audit_intrabar_quality
from galapagos.research.intrabar.gap_analysis import analyze_signal_gap_impact


def test_data_quality_gap_detection():
    # Create mock data with a gap
    df = pd.DataFrame({
        "timestamp": [
            pd.Timestamp("2024-01-01 00:00:00"),
            pd.Timestamp("2024-01-01 00:05:00"),
            pd.Timestamp("2024-01-02 00:00:00"), # 1 day gap
            pd.Timestamp("2024-01-02 00:05:00"),
        ],
        "open": [10, 11, 12, 13],
        "high": [11, 12, 13, 14],
        "low": [9, 10, 11, 12],
        "close": [10.5, 11.5, 12.5, 13.5],
        "volume": [100, 110, 120, 130]
    })
    
    # Save to temp parquet for the audit tool
    tmp_path = "tests/mock_intrabar_gap.parquet"
    df.to_parquet(tmp_path)
    
    result = audit_intrabar_quality(tmp_path)
    
    assert result["status"] == "INTRABAR_DATA_HAS_GAPS"
    assert not result["usable_for_continuous_backtest"]
    assert result["usable_for_gap_aware_signal_eval"]
    assert result["largest_gap_seconds"] == 86400 - 300 # 1 day minus 5min? Wait.
    # diff between 00:05 and 00:00 is 23h55
    assert result["gaps_count"] == 1


def test_gap_impact_analysis():
    signals = pd.DataFrame({
        "timestamp": [
            pd.Timestamp("2024-01-01 00:02:00"), # Covered
            pd.Timestamp("2024-01-01 12:00:00"), # Gap
            pd.Timestamp("2024-01-02 00:02:00"), # Covered
        ]
    })
    
    intrabar = pd.DataFrame({
        "timestamp": [
            pd.Timestamp("2024-01-01 00:00:00"),
            pd.Timestamp("2024-01-01 00:05:00"),
            pd.Timestamp("2024-01-02 00:00:00"),
            pd.Timestamp("2024-01-02 00:05:00"),
        ]
    })
    
    # Use UTC for consistency if needed, but here we just need them to match
    signals["timestamp"] = pd.to_datetime(signals["timestamp"], utc=True)
    intrabar["timestamp"] = pd.to_datetime(intrabar["timestamp"], utc=True)
    
    result = analyze_signal_gap_impact(signals, intrabar)
    
    assert result["total_signals"] == 3
    assert result["covered_signals"] == 2
    assert result["gap_signals"] == 1
    assert "GAP_AWARE_EVALUATION_REQUIRED" in result["verdict"]
