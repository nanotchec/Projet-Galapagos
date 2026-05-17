from __future__ import annotations

import pandas as pd

from galapagos.research.ensemble.leakage_audit import audit_ensemble_leakage


def test_leakage_audit_detects_forbidden_columns():
    df_dataset = pd.DataFrame()
    df_preds = pd.DataFrame({
        "timestamp": range(20),
        "split_name": ["test_1"] * 20,
        "predicted_probability": [0.1, 0.9] * 10,
        "actual_target": [0.1, 0.9] * 10 # Perfectly correlated
    })
    
    res = audit_ensemble_leakage(df_dataset, df_preds)
    assert res["status"] == "ENSEMBLE_LEAKAGE_AUDIT_FAILED"
    assert any("correlation" in c for c in res["checks"])

def test_leakage_audit_returns_limited_if_not_strictly_oos():
    df_dataset = pd.DataFrame()
    df_preds = pd.DataFrame({
        "timestamp": range(5),
        "predicted_probability": [0.5] * 5
        # split_name is missing
    })
    
    res = audit_ensemble_leakage(df_dataset, df_preds)
    assert res["status"] == "ENSEMBLE_LEAKAGE_AUDIT_LIMITED"
    assert "split_name column missing" in res["checks"][0]

def test_horizon_separation_logic():
    # Simple check that we can filter model_cols by horizon
    cols = ["rf_target_up_after_cost_6bar", "gb_target_up_after_cost_12bar", "rf_target_up_after_cost_12bar"]
    
    horizon_6 = [c for c in cols if "_target_up_after_cost_6bar" in c]
    horizon_12 = [c for c in cols if "_target_up_after_cost_12bar" in c]
    
    assert len(horizon_6) == 1
    assert "rf_target_up_after_cost_6bar" in horizon_6
    assert len(horizon_12) == 2
    assert "gb_target_up_after_cost_12bar" in horizon_12
    assert "rf_target_up_after_cost_12bar" in horizon_12
    assert "rf_target_up_after_cost_6bar" not in horizon_12
