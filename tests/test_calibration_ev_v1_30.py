from __future__ import annotations

import pandas as pd
import numpy as np
import pytest
from galapagos.research.calibration_ev.point_in_time_audit import audit_point_in_time_features
from galapagos.research.calibration_ev.calibration_metrics import calculate_calibration_metrics
from galapagos.research.calibration_ev.prediction_frame_builder import build_prediction_frames
from galapagos.research.calibration_ev.expected_value_proxy import calculate_ev_proxy

def test_point_in_time_audit_semantics():
    df = pd.DataFrame({
        "timestamp": [1, 2],
        "predicted_probability": [0.6, 0.7],
        "forward_return_12bar": [0.01, -0.01]
    })
    # Case 1: Raw audit sees outcomes but they are classified
    audit = audit_point_in_time_features(df)
    assert audit["point_in_time_status"] == "POINT_IN_TIME_AUDIT_PASSED_WITH_CLASSIFIED_OUTCOMES"
    assert audit["raw_dataset_contains_outcomes"] is True
    
    # Case 2: Selection audit fails if forbidden columns are included
    selection_audit = audit_point_in_time_features(df, selection_cols=df.columns.tolist())
    assert selection_audit["point_in_time_status"] == "POINT_IN_TIME_AUDIT_FAILED_SELECTION_LEAKAGE"
    assert "forward_return_12bar" in selection_audit["selection_frame_forbidden_columns"]

def test_prediction_frame_separation_hardened():
    df = pd.DataFrame({
        "timestamp": [1, 2],
        "predicted_probability": [0.6, 0.7],
        "forward_return_12bar": [0.01, -0.01],
        "model_name": ["m1", "m1"]
    })
    selection, outcome, integrity = build_prediction_frames(df)
    assert "forward_return_12bar" not in selection.columns
    assert "forward_return_12bar" in outcome.columns
    assert integrity["integrity_status"] == "PREDICTION_FRAME_INTEGRITY_PASSED"
    assert integrity["selection_frame_status"] == "POINT_IN_TIME_AUDIT_PASSED"

def test_cost_model_partial_status():
    from galapagos.research.calibration_ev.cost_model_foundation import audit_cost_model_foundation
    df = pd.DataFrame({"cost_adjusted_forward_return": [0.01]})
    res = audit_cost_model_foundation(df)
    assert res["cost_model_status"] == "COST_MODEL_FOUNDATION_PARTIAL_COST_ADJUSTED_RETURN_ONLY"
    assert res["costs_isolated_from_gross"] is False

def test_validator_fails_on_diagnostic_failure(tmp_path):
    import sys
    import os
    import json
    sys.path.append(os.path.abspath("scripts"))
    from validate_calibration_ev_reports import validate_reports
    
    # Create fake reports where one has a FAILED status
    os.makedirs(tmp_path, exist_ok=True)
    report_keys = [
        "point_in_time_feature_audit", "prediction_frame_integrity", 
        "calibration_global", "reliability_bins", "calibration_temporal",
        "calibration_regime", "payoff_asymmetry", "cost_model_foundation",
        "expected_value_proxy", "calibration_ev_summary", "recommendation"
    ]
    for key in report_keys:
        suffix = "v1_30_2"
        fname = f"{suffix}_{key}.json" if key == "recommendation" else f"{key}_{suffix}.json"
        
        stat_key = "status"
        if key == "point_in_time_feature_audit": stat_key = "point_in_time_status"
        elif key == "prediction_frame_integrity": stat_key = "integrity_status"
        elif key == "cost_model_foundation": stat_key = "cost_model_status"
        
        content = {stat_key: "FAILED" if key == "point_in_time_feature_audit" else "PASSED"}
        if key == "calibration_global": content.update({"brier_score": 0.1, "ece": 0.05})
        if key == "calibration_ev_summary": content.update({"calibration_global_status": "PASSED", "ev_proxy_status": "PASSED"})
        if key == "recommendation": content.update({"no_real_trading": True, "no_preregistration_yet": True, "no_paper_live": True, "ready_for_reviewer": False, "holdout_executed": False})
        
        with open(tmp_path / fname, "w") as f:
            json.dump(content, f)
            
    res = validate_reports("v1.30.2", report_dir=str(tmp_path))
    assert res["status"] == "CALIBRATION_EV_REPORTS_INCONSISTENT"
    assert any("point_in_time_status FAILED" in issue for issue in res["issues"])

def test_brier_score_computation():
    y_true = np.array([0, 1, 1, 0])
    y_prob = np.array([0.1, 0.9, 0.8, 0.2])
    metrics = calculate_calibration_metrics(y_true, y_prob)
    assert metrics["brier_score"] < 0.1
    assert "ece" in metrics

def test_ev_proxy_warning():
    selection = pd.DataFrame({"predicted_probability": [0.8, 0.9]})
    outcome = pd.DataFrame({"forward_return_12bar": [0.05, 0.05]})
    results = calculate_ev_proxy(selection, outcome)
    for r in results:
        assert r["ev_proxy_diagnostic_only"] is True
        assert r["uses_uncalibrated_probability"] is True

def test_recommendation_blocks_trading():
    from galapagos.research.calibration_ev.recommendation_engine import generate_v1_30_recommendations
    recs = generate_v1_30_recommendations({})
    assert recs["no_real_trading"] is True
    assert recs["no_money_deployment"] is True
    assert recs["ready_for_reviewer"] is False

def test_safety_constraints_no_real_trading():
    import os
    assert os.environ.get("REAL_TRADING_ENABLED") != "true"
