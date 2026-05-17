import pytest
import pandas as pd
from typing import Any

from galapagos.research.paper_forward.protocol_loader import load_and_verify_protocol
from galapagos.research.paper_forward.frozen_filter import apply_frozen_filter, validate_filter_definition
from galapagos.research.paper_forward.validation_engine import compute_realized_metrics

def test_protocol_loader_accepts_v1_26_6():
    # Use a mock dict to simulate protocol
    protocol = {
        "protocol_version": "v1.26.6",
        "reference_protocol": True,
        "protocol_locked": True,
        "filter_parameters_locked": True,
        "policy_parameters_locked": True,
        "selection_rules_locked": True,
        "metrics_locked": True,
        "data_sources_locked": True,
        "cost_model_locked": True,
        "baselines_locked": True,
        "no_hyperparameter_tuning": True,
        "no_reviewer_llm": True,
        "no_holdout": True,
        "no_real_trading": True
    }
    # To test load_and_verify we'd need to mock open, but we can just test the logic inside if we extracted it.
    # Since load_and_verify_protocol reads from file, let's create a temp file for testing
    import json
    import tempfile
    
    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        json.dump(protocol, f)
        path = f.name
        
    res = load_and_verify_protocol(path)
    assert res["status"] == "PROTOCOL_CHECK_PASSED_REFERENCE_V1_26_6"
    assert res["protocol"]["reference_protocol"] is True

def test_protocol_loader_rejects_non_reference():
    protocol = {
        "protocol_version": "v1.26.2", # Non-reference
        "reference_protocol": False,
        "protocol_locked": True,
        # ... other locks omitted for brevity, let's assume they are present
        "filter_parameters_locked": True,
        "policy_parameters_locked": True,
        "selection_rules_locked": True,
        "metrics_locked": True,
        "data_sources_locked": True,
        "cost_model_locked": True,
        "baselines_locked": True,
        "no_hyperparameter_tuning": True,
        "no_reviewer_llm": True,
        "no_holdout": True,
        "no_real_trading": True
    }
    import json
    import tempfile
    
    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        json.dump(protocol, f)
        path = f.name
        
    res = load_and_verify_protocol(path)
    assert res["status"] == "PROTOCOL_CHECK_FAILED"
    assert any("reference_protocol" in issue for issue in res["issues"])

def test_frozen_filter_reconstructs_highest_score_per_period():
    protocol = {
        "candidate_filter": "low_frequency_strict_score",
        "locked_filter_definition": {
            "score_column": "predicted_probability",
            "selection_logic": "highest_score_per_period",
            "temporal_frequency_rule": "7D",
            "threshold": None,
            "threshold_type": "none"
        }
    }
    
    data = {
        "timestamp": pd.to_datetime([
            "2026-05-01T10:00:00", 
            "2026-05-02T10:00:00",
            "2026-05-10T10:00:00", # New 7D period
            "2026-05-11T10:00:00"
        ]),
        "predicted_probability": [0.6, 0.8, 0.9, 0.7],
        "other_col": [1, 2, 3, 4]
    }
    df = pd.DataFrame(data)
    
    selected = apply_frozen_filter(df, protocol)
    
    assert len(selected) == 2
    # Should pick index 1 (0.8) and index 2 (0.9)
    assert set(selected.index) == {1, 2}
    assert "other_col" in selected.columns

def test_frozen_filter_validation_no_threshold():
    protocol = {
        "locked_filter_definition": {
            "filter_name": "low_frequency_strict_score",
            "score_column": "predicted_probability",
            "selection_logic": "highest_score_per_period",
            "temporal_frequency_rule": "7D",
            "threshold": None,
            "threshold_type": "none",
            "causal_only": True,
            "tie_break_explicit": False,
            "tie_break_warning": "Warning: historical"
        }
    }
    
    res = validate_filter_definition(protocol)
    assert res["exact_filter_reconstructable"] is True
    assert res["status"] == "FROZEN_FILTER_AUDIT_PASSED_WITH_TIE_BREAK_WARNING"

def test_validation_engine_status_no_oos():
    # Test compute realized metrics logic
    empty_df = pd.DataFrame()
    metrics = compute_realized_metrics(empty_df)
    assert metrics["selected_count"] == 0
    assert metrics["status"] == "NO_TRADES_SELECTED"

def test_validation_engine_60_trades_rule():
    # If selected count is < 60, status must be INCONCLUSIVE_NEEDS_MORE_DATA
    from galapagos.research.paper_forward.validation_engine import run_paper_forward_validation
    
    protocol = {
        "candidate_filter": "low_frequency_strict_score",
        "locked_filter_definition": {
            "score_column": "predicted_probability",
            "selection_logic": "highest_score_per_period",
            "temporal_frequency_rule": "7D"
        }
    }
    
    # Generate 5 trades
    data = {
        "timestamp": pd.date_range("2026-05-10", periods=5, freq="7D"),
        "predicted_probability": [0.8] * 5
    }
    df = pd.DataFrame(data)
    
    # ref timestamp before data
    res = run_paper_forward_validation(
        protocol, {}, df, pd.DataFrame(), pd.DataFrame(), "2026-05-01T00:00:00Z"
    )
    
    assert res["selected_count"] == 5
    assert res["criteria_status"] == "INCONCLUSIVE_NEEDS_MORE_DATA"
    assert res["strategy_validated"] is False
    assert res["minimum_required_selected_trades"] == 60
