import pytest
import pandas as pd
from galapagos.research.causality_audit.rule_semantics import analyze_rule_semantics
from galapagos.research.causality_audit.lookahead_detector import detect_selection_lookahead
from galapagos.research.causality_audit.live_executability import audit_live_executability

def test_static_audit_detects_weekly_top_as_non_causal():
    protocol = {
        "locked_filter_definition": {
            "filter_name": "low_frequency_strict_score",
            "selection_logic": "highest_score_per_period",
            "temporal_frequency_rule": "7D"
        }
    }
    res = analyze_rule_semantics(protocol, {})
    assert res["uses_full_period_scores"] is True
    assert res["static_causality_status"] == "NON_CAUSAL_FULL_PERIOD_SELECTION"

def test_static_audit_detects_cooldown_as_causal():
    # Cooldown (first-come-first-served) is causal
    protocol = {
        "locked_filter_definition": {
            "filter_name": "one_trade_per_day",
            "selection_logic": "cooldown",
            "temporal_frequency_rule": "24h"
        }
    }
    res = analyze_rule_semantics(protocol, {})
    assert res["uses_full_period_scores"] is False
    assert res["static_causality_status"] == "CAUSAL_BY_CONSTRUCTION"

def test_lookahead_detector_flags_early_selection():
    # Monday and Tuesday are definitely in the same 7D period regardless of floor origin
    predictions = pd.DataFrame({
        "timestamp": pd.to_datetime(["2026-05-04", "2026-05-05"], utc=True),
        "predicted_probability": [0.9, 0.8]
    })
    protocol = {
        "locked_filter_definition": {
            "score_column": "predicted_probability",
            "temporal_frequency_rule": "7D"
        }
    }
    res = detect_selection_lookahead(predictions, protocol)
    assert res["lookahead_status"] == "INTRA_PERIOD_LOOKAHEAD_DETECTED"
    assert res["selections_requiring_future_score_visibility"] == 1

def test_live_executability_classification():
    static_audit = {"uses_full_period_scores": True, "decision_time": "after_period_known"}
    res = audit_live_executability(static_audit)
    assert res["classification"] == "RETROSPECTIVE_ONLY"
    assert res["live_executable_as_written"] is False
