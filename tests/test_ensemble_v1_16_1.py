from __future__ import annotations

import pandas as pd
import pytest

from galapagos.research.ensemble.candidate_builder import build_reviewer_candidates
from galapagos.research.ensemble.evaluation import evaluate_ensemble_bucket
from galapagos.research.ensemble.leakage_audit import audit_ensemble_leakage


def test_evaluate_ensemble_bucket_separation():
    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=100, freq="4h"),
        "score": [0.1] * 90 + [0.9] * 10,
        "target": [0] * 95 + [1] * 5, # Hit rate 50% in top 10
        "fwd_ret": [0.0] * 95 + [0.02] * 5, # 0.01 mean return in top 10
    })
    
    res = evaluate_ensemble_bucket(
        df, "score", "target", "fwd_ret", top_pct=0.1
    )
    
    assert res["status"] == "completed"
    assert res["count"] == 10
    assert res["hit_rate_target"] == 0.5
    assert res["mean_forward_return"] == pytest.approx(0.01)
    # Cost adjustment (manual fallback)
    assert res["mean_cost_adjusted_forward_return"] == pytest.approx(0.01 - 0.003)

def test_leakage_audit_detects_train():
    df_dataset = pd.DataFrame()
    df_preds = pd.DataFrame({
        "timestamp": [1, 2],
        "split_name": ["train_fold_1", "test_fold_1"],
        "predicted_probability": [0.5, 0.6]
    })
    
    res = audit_ensemble_leakage(df_dataset, df_preds)
    assert res["status"] == "ENSEMBLE_LEAKAGE_AUDIT_FAILED"
    assert any("train" in c for c in res["checks"])

def test_leakage_audit_detects_high_corr():
    df_dataset = pd.DataFrame()
    df_preds = pd.DataFrame({
        "timestamp": range(20),
        "split_name": ["test_1"] * 20,
        "predicted_probability": [0.1, 0.9] * 10,
        "actual_target": [0.1, 0.9] * 10
    })
    
    res = audit_ensemble_leakage(df_dataset, df_preds)
    assert res["status"] == "ENSEMBLE_LEAKAGE_AUDIT_FAILED"
    assert any("correlation" in c for c in res["checks"])

def test_candidate_builder_no_expected_return_proxy():
    df = pd.DataFrame({
        "timestamp": [pd.Timestamp("2024-01-01")],
        "score": [0.8],
        "agreement": [0.9],
        "combined_alpha_score": [0.7],
        "macro_regime_score": [0.1],
        "derivatives_regime_score": [-0.1]
    })
    
    import os
    path = "tests/temp_candidates.jsonl"
    build_reviewer_candidates(df, "score", "agreement", path)
    
    import json
    with open(path) as f:
        data = json.loads(f.readline())
        
    assert "expected_forward_return_proxy" not in data["quant_evidence"]
    assert "probability_edge_over_50" in data["quant_evidence"]
    assert "historical_bucket_mean_forward_return" in data["quant_evidence"]
    
    if os.path.exists(path):
        os.remove(path)
