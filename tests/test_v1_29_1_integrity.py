from __future__ import annotations

import pandas as pd
import pytest
from galapagos.research.causal_signal_research.causal_filter_evaluator import evaluate_filter_performance
from galapagos.research.causal_signal_research.signal_dedup_audit import apply_dedup_policy, audit_signal_dedup

def test_data_separation_evaluation():
    selection_frame = pd.DataFrame({
        "timestamp": pd.to_datetime(["2026-01-01 00:00"]),
        "predicted_probability": [0.7]
    })
    outcome_frame = pd.DataFrame({
        "timestamp": pd.to_datetime(["2026-01-01 00:00"]),
        "net_pnl_pct": [0.05]
    })
    
    mask = pd.Series([True], index=[0])
    perf = evaluate_filter_performance(mask, selection_frame, outcome_frame)
    
    assert perf["selected_count"] == 1
    assert "net_mean_pnl" in perf
    assert perf["net_mean_pnl"] == 0.05

def test_signal_dedup():
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(["2026-01-01 00:00", "2026-01-01 00:00", "2026-01-01 04:00"]),
        "predicted_probability": [0.7, 0.8, 0.7],
        "model_name": ["model_A", "model_B", "model_A"]
    })
    
    deduped = apply_dedup_policy(df)
    assert len(deduped) == 2
    assert deduped.iloc[0]["model_name"] == "model_A" # First stable

def test_dedup_audit():
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(["2026-01-01 00:00", "2026-01-01 00:00"]),
        "predicted_probability": [0.7, 0.8]
    })
    audit = audit_signal_dedup(df)
    assert audit["duplicate_timestamp_rows"] == 2
    assert audit["rows_per_timestamp_max"] == 2
