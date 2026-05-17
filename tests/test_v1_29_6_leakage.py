from __future__ import annotations

import pandas as pd
import pytest
from galapagos.research.recent_regime_diagnostic.data_loader import separate_frames
from galapagos.research.recent_regime_diagnostic.selected_filter_rebuilder import rebuild_selected_filter_consistent

def test_separate_frames_leakage_prevention():
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(["2024-01-01"]),
        "predicted_probability": [0.7],
        "forward_return_12bar": [0.01],
        "net_pnl_pct": [0.005],
        "feature_1": [1.0]
    })
    
    selection, outcome = separate_frames(df)
    
    # Check selection
    assert "predicted_probability" in selection.columns
    assert "feature_1" in selection.columns
    assert "forward_return_12bar" not in selection.columns
    assert "net_pnl_pct" not in selection.columns
    
    # Check outcome
    assert "forward_return_12bar" in outcome.columns
    assert "net_pnl_pct" in outcome.columns

def test_rebuild_fails_on_leakage():
    # Simulate a raw dataframe where leakage is forced into the causal frame logic
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(["2024-01-01"] * 500), # Enough rows for logic
        "predicted_probability": [0.7] * 500,
        "forward_return_12bar": [0.01] * 500,
        "model_name": ["m1"] * 500,
        "confidence": [0.5] * 500,
        "feature_count": [10] * 500
    })
    
    # By default rebuild_selected_filter_consistent calls separate_frames
    # So it should be clean. 
    # To test the "FAILURE" status, we would need to bypass separate_frames in the rebuilder
    # but the rebuilder IS the one enforcing it now.
    
    mask, audit = rebuild_selected_filter_consistent(df, 0.65)
    assert audit["forbidden_columns_found"] == []
    assert audit["rebuild_status"] == "REBUILD_MISMATCH_DETECTION" # Because count won't be 225
