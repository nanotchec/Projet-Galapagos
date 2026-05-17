"""Tests for Galapagos V1.21.2 Gap-Aware logic and fixed reports."""
from __future__ import annotations

import pandas as pd

from galapagos.research.intrabar.gap_analysis import analyze_signal_gap_impact


def test_gap_analysis_granularity():
    # Signals with duplicate timestamps (raw rows vs unique)
    signals = pd.DataFrame({
        "timestamp": [
            pd.Timestamp("2024-01-01 00:02:00"), # Covered
            pd.Timestamp("2024-01-01 00:02:00"), # Duplicate (raw)
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
    
    signals["timestamp"] = pd.to_datetime(signals["timestamp"], utc=True)
    intrabar["timestamp"] = pd.to_datetime(intrabar["timestamp"], utc=True)
    
    result = analyze_signal_gap_impact(signals, intrabar)
    
    # Raw rows: 2 covered (duplicates of same covered TS), 1 gap, 1 covered = 3 covered, 1 gap
    assert result["raw_prediction_rows_total"] == 4
    assert result["raw_prediction_rows_in_gap"] == 1
    
    # Unique TS: 2024-01-01 00:02 (cov), 2024-01-01 12:00 (gap), 
    # 2024-01-02 00:02 (cov) = 2 cov, 1 gap
    assert result["unique_signal_timestamps_total"] == 3
    assert result["unique_signal_timestamps_in_gap"] == 1
    assert result["unique_signal_timestamps_gap_ratio"] == 1/3
    
    assert "GAP_IMPACT_SIGNIFICANT" in result["verdict"]
