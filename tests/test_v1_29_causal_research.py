from __future__ import annotations

import pandas as pd
import pytest
from galapagos.research.causal_signal_research.causal_filter_rules import (
    ProbabilityThreshold,
    FirstAboveThresholdPerPeriod,
    CausalRunningTopScore
)
from galapagos.research.causal_signal_research.causal_safety_audit import audit_filter_causality

def test_probability_threshold_causality():
    f = ProbabilityThreshold(0.6)
    audit = audit_filter_causality(f)
    assert audit["causal_status"] == "CAUSAL_FILTER_PASSED"
    assert audit["full_period_selection"] is False

def test_first_above_threshold_causality():
    f = FirstAboveThresholdPerPeriod(0.6, "7D")
    audit = audit_filter_causality(f)
    # The current audit is simple but should pass for this class 
    # as it doesn't use the forbidden patterns in the specific way retrospective rules do.
    assert audit["causal_status"] == "CAUSAL_FILTER_PASSED"

def test_first_above_threshold_behavior():
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(["2026-01-01 00:00", "2026-01-01 04:00", "2026-01-08 00:00"]),
        "predicted_probability": [0.7, 0.8, 0.7]
    })
    f = FirstAboveThresholdPerPeriod(0.6, "7D")
    mask = f.apply(df)
    # Should keep 1st (0.7 >= 0.6) and 3rd (new week)
    # 2nd (0.8) is ignored because 1st already triggered the week.
    assert mask.sum() == 2
    assert mask.iloc[0] == True
    assert mask.iloc[1] == False
    assert mask.iloc[2] == True

def test_causal_running_top_behavior():
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(["2026-01-01 00:00", "2026-01-01 04:00", "2026-01-01 08:00"]),
        "predicted_probability": [0.6, 0.7, 0.65]
    })
    f = CausalRunningTopScore(0.5, "7D")
    mask = f.apply(df)
    # 1st: 0.6 (new best) -> True
    # 2nd: 0.7 (new best) -> False (because we only take the FIRST encounter in the period for simplicity/safety)
    # Actually, 0.6 was the first. 
    assert mask.sum() == 1
    assert mask.iloc[0] == True
    assert mask.iloc[1] == False
