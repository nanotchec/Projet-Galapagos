from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from galapagos.research.walk_forward_calibration.split_builder import build_walk_forward_splits
from galapagos.research.walk_forward_calibration.platt_calibrator import PlattCalibrator
from galapagos.research.walk_forward_calibration.isotonic_calibrator import IsotonicCalibrator
from galapagos.research.walk_forward_calibration.bin_calibrator import BinCalibrator
from galapagos.research.walk_forward_calibration.calibration_metrics import get_calibration_metrics
from galapagos.research.walk_forward_calibration.leakage_audit import audit_walk_forward_leakage


def test_walk_forward_splits_no_overlap():
    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=1000, freq="D")
    })
    df["timestamp"] = df["timestamp"].astype(str)
    splits = build_walk_forward_splits(df)
    
    for split in splits:
        assert split.train_end < split.test_start
        assert split.test_start < split.test_end


def test_calibrators_fit_predict():
    y_true = np.array([0, 1, 0, 1, 0, 1])
    y_prob = np.array([0.1, 0.9, 0.2, 0.8, 0.3, 0.7])
    
    methods = [PlattCalibrator(), IsotonicCalibrator(), BinCalibrator(n_bins=2)]
    
    for method in methods:
        method.fit(y_true, y_prob)
        y_cal = method.predict(y_prob)
        assert len(y_cal) == len(y_prob)
        assert np.all(y_cal >= 0) and np.all(y_cal <= 1)


def test_leakage_audit_detects_overlap():
    train_df = pd.DataFrame({"timestamp": ["2024-01-01", "2024-02-01"]})
    test_df = pd.DataFrame({"timestamp": ["2024-01-15", "2024-03-01"]})
    
    audit = audit_walk_forward_leakage(train_df, test_df, ["prob"])
    assert audit["temporal_overlap"] is True
    assert audit["leakage_status"] == "WALK_FORWARD_CALIBRATION_TEMPORAL_OVERLAP_DETECTED"


def test_safety_constraints():
    # V1.31 specific safety checks in recommendation
    from galapagos.research.walk_forward_calibration.recommendation_engine import generate_v1_31_recommendation
    recs = generate_v1_31_recommendation({"calibration_improves_ece": True})
    assert recs["no_real_trading"] is True
    assert recs["no_paper_live"] is True
    assert recs["ready_for_reviewer"] is False
