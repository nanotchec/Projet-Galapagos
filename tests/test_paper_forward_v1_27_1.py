import pytest
import pandas as pd
from pathlib import Path
from galapagos.research.paper_forward.data_availability import check_data_availability
from galapagos.research.paper_forward.frozen_filter import apply_frozen_filter
from galapagos.research.paper_forward.criteria_evaluator import evaluate_success_criteria
from galapagos.research.paper_forward.validation_engine import run_paper_forward_validation

def test_data_availability_multi_column(tmp_path):
    # Test with 'available_timestamp'
    p = tmp_path / "test.parquet"
    df = pd.DataFrame({"available_timestamp": [pd.Timestamp("2026-05-07")]})
    df.to_parquet(p)
    
    res = check_data_availability(str(p), "missing.parquet", "missing.parquet")
    assert res["timestamp_column_used"]["predictions"] == "available_timestamp"
    assert res["has_new_out_of_sample_data"] is True

def test_frozen_filter_no_threshold():
    protocol = {
        "candidate_filter": "low_frequency_strict_score",
        "locked_filter_definition": {"score_column": "score"}
        # Missing threshold
    }
    candidates = pd.DataFrame({"score": [1.0]})
    selected = apply_frozen_filter(candidates, protocol)
    assert selected.empty

def test_criteria_evaluator_not_evaluated():
    metrics = {"selected_count": 100, "mean_net_pnl_after_cost_pct": None}
    criteria = {}
    res = evaluate_success_criteria(metrics, criteria)
    assert res["status"] == "NOT_EVALUATED_MISSING_METRICS"
    assert res["detailed_results"]["mean_net_pnl"]["status"] == "NOT_EVALUATED"

def test_validation_engine_no_mock():
    # If no outcome columns, should not invent results
    protocol = {
        "candidate_filter": "low_frequency_strict_score",
        "locked_filter_definition": {"score_column": "score", "threshold": 0.5}
    }
    preds = pd.DataFrame({
        "timestamp": [pd.Timestamp("2026-05-07")],
        "score": [0.9]
    })
    res = run_paper_forward_validation(protocol, {}, preds, pd.DataFrame(), pd.DataFrame())
    assert res["validation_executed"] is False
    assert res["reason"] == "OOS_OUTCOMES_NOT_AVAILABLE"
    # selected_count < 60 takes precedence in status
    assert res["detailed_eval"]["status"] == "INCONCLUSIVE_NEEDS_MORE_DATA"
