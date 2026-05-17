import pandas as pd
import pytest
from galapagos.research.canonical_universe.universe_builder import build_canonical_universe
from galapagos.research.canonical_universe.universe_schema import FORBIDDEN_SELECTION_COLUMNS

def test_selection_frame_is_clean():
    # Setup
    df_preds = pd.DataFrame({
        "timestamp": pd.to_datetime(["2026-01-01 00:00:00"]).tz_localize(None),
        "predicted_probability": [0.6],
        "pnl": [0.01] # Forbidden column
    })
    df_dataset = pd.DataFrame({
        "timestamp": pd.to_datetime(["2026-01-01 00:00:00"]).tz_localize(None),
        "feature_1": [1.0]
    })
    
    result = build_canonical_universe(df_preds, df_dataset, version="test")
    df_selection = result["selection_frame"]
    
    # Assert
    for col in FORBIDDEN_SELECTION_COLUMNS:
        assert col not in df_selection.columns
    assert "pnl" not in df_selection.columns

def test_outcome_frame_is_separate():
    df_preds = pd.DataFrame({
        "timestamp": pd.to_datetime(["2026-01-01 00:00:00"]).tz_localize(None),
        "predicted_probability": [0.6],
        "pnl": [0.01]
    })
    df_dataset = pd.DataFrame({
        "timestamp": pd.to_datetime(["2026-01-01 00:00:00"]).tz_localize(None),
        "actual_target": [1]
    })
    
    result = build_canonical_universe(df_preds, df_dataset, version="test")
    df_outcome = result["outcome_frame"]
    
    assert "pnl" in df_outcome.columns
    assert "actual_target" in df_outcome.columns
    assert "predicted_probability" not in df_outcome.columns

def test_warmup_marking_no_drop():
    df_preds = pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=150, freq="4h").tz_localize(None),
        "predicted_probability": [0.6] * 150
    })
    df_dataset = pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=150, freq="4h").tz_localize(None),
        "feature_1": [1.0] * 150
    })
    
    result = build_canonical_universe(df_preds, df_dataset, version="v1.36.8")
    reports = result["reports"]
    
    assert reports["counts"]["count_semantics_version"] == "v1.36.8_explicit"
    assert reports["ev_feature_audit"]["ev_feature_status"] == "EV_FEATURES_NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE"

def test_audit_recommendation_evidence():
    # Placeholder for audit evidence test
    pass
