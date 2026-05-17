from __future__ import annotations

import pandas as pd

from galapagos.research.ensemble.agreement import analyze_agreement_buckets
from galapagos.research.ensemble.leakage_audit import audit_ensemble_leakage


def test_leakage_audit_returns_limited_if_split_contains_train():
    df_dataset = pd.DataFrame()
    df_preds = pd.DataFrame({
        "timestamp": range(5),
        "split_name": ["test_train_2022"] * 5, # Contains 'train'
        "predicted_probability": [0.5] * 5
    })
    
    res = audit_ensemble_leakage(df_dataset, df_preds)
    assert res["status"] == "ENSEMBLE_LEAKAGE_AUDIT_LIMITED"
    assert "contains 'train'" in res["checks"][0]

def test_agreement_verdict_economic_edge():
    df = pd.DataFrame({
        "agreement": [0.9] * 10,
        "return": [0.001] * 10 # 0.001 - 0.003 = -0.002 (negative)
    })
    
    # We need to compute agreement_bucket first if we test the internal logic, 
    # but let's test the return value of analyze_agreement_buckets
    stats_df, verdict = analyze_agreement_buckets(df, "agreement", "return", cost_threshold=0.003)
    
    assert verdict == "AGREEMENT_NO_ECONOMIC_EDGE"

def test_agreement_verdict_improves_signal():
    df = pd.DataFrame({
        "agreement": [0.9] * 10,
        "return": [0.005] * 10 # 0.005 - 0.003 = 0.002 (positive)
    })
    
    stats_df, verdict = analyze_agreement_buckets(df, "agreement", "return", cost_threshold=0.003)
    
    assert verdict == "AGREEMENT_IMPROVES_SIGNAL"
