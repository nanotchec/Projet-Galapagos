"""Tests for ML hardening V1.15.1."""
from __future__ import annotations

import numpy as np
import pandas as pd

from galapagos.research.ml.leakage_audit import audit_ml_leakage
from galapagos.research.ml.permutation import run_permutation_test
from galapagos.research.ml.random_trading_baselines import (
    random_entries_same_count,
)
from galapagos.research.ml.regime_robustness import analyze_regime_robustness
from galapagos.research.ml.top_bucket_analysis import analyze_top_bucket
from galapagos.research.ml.walk_forward import (
    build_date_based_walk_forward_splits,
)


def _mock_dataset() -> pd.DataFrame:
    rng = np.random.RandomState(42)
    n = 1000
    close = 100.0 + np.cumsum(rng.randn(n) * 0.5)
    return pd.DataFrame({
        "timestamp": pd.date_range("2022-01-01", periods=n, freq="4h", tz="UTC"),
        "close": close,
        "forward_return_12bar": rng.randn(n) * 0.01,
        "target_up_after_cost_12bar": rng.choice([0.0, 1.0], size=n),
        "realized_vol_42": rng.rand(n),
        "trend_slope_42": rng.randn(n),
        "feature_1": rng.randn(n),
        "feature_2": rng.randn(n),
    })


def test_date_based_splits() -> None:
    df = _mock_dataset()
    config = {
        "walk_forward": {
            "method": "date_based",
            "embargo_bars": 6,
            "date_windows": [
                {
                    "name": "test_win",
                    "train_start": "2022-01-01",
                    "train_end": "2022-02-01",
                    "test_start": "2022-03-01",
                    "test_end": "2022-04-01",
                }
            ]
        }
    }
    windows = build_date_based_walk_forward_splits(df, config)
    assert len(windows) == 1
    w = windows[0]
    assert w.name == "test_win"
    assert w.train_start < w.train_end
    assert w.train_end + 6 <= w.test_start
    assert w.test_start < w.test_end


def test_leakage_audit() -> None:
    df = _mock_dataset()
    
    # Missing features
    res = audit_ml_leakage(df, [], "target_up_after_cost_12bar", [0, 1], [2, 3])
    assert res["status"] == "ML_LEAKAGE_RISK_FOUND"
    
    # Target in features
    res = audit_ml_leakage(df, ["feature_1", "target_up_after_cost_12bar"], "target_up_after_cost_12bar", [0, 1], [2, 3])
    assert res["status"] == "ML_FEATURE_COLUMNS_UNSAFE"
    
    # Forward in features
    res = audit_ml_leakage(df, ["feature_1", "forward_return_12bar"], "target_up_after_cost_12bar", [0, 1], [2, 3])
    assert res["status"] == "ML_FEATURE_COLUMNS_UNSAFE"
    
    # Overlap
    res = audit_ml_leakage(df, ["feature_1"], "target_up_after_cost_12bar", [0, 1, 2], [2, 3, 4])
    assert res["status"] == "ML_SPLIT_UNSAFE"
    assert res["reason"] == "train_test_overlap"
    
    # Non-chronological
    res = audit_ml_leakage(df, ["feature_1"], "target_up_after_cost_12bar", [2, 3], [0, 1])
    assert res["status"] == "ML_SPLIT_UNSAFE"
    assert res["reason"] == "train_after_test_starts"
    
    # Pass
    res = audit_ml_leakage(df, ["feature_1"], "target_up_after_cost_12bar", [0, 1], [2, 3])
    assert res["status"] == "ML_LEAKAGE_AUDIT_PASSED"


def test_random_trading_baselines() -> None:
    df = _mock_dataset()
    res = random_entries_same_count(df, entry_count=50, n_trials=100)
    assert res["status"] == "computed"
    assert res["entry_count"] == 50
    assert "mean_forward_return" in res
    assert "distribution_percentiles" in res


def test_permutation() -> None:
    class DummyModel:
        def fit(self, x, y): pass
        def predict(self, x): return np.zeros(len(x))
        
    x = np.random.randn(100, 2)
    y = np.random.choice([0, 1], size=100)
    res = run_permutation_test(DummyModel(), x[:50], y[:50], x[50:], y[50:], n_permutations=10)
    assert res["status"] == "computed"
    assert "p_value_approx" in res


def test_top_bucket() -> None:
    y_proba = np.linspace(0.1, 0.9, 100)
    returns = np.random.randn(100)
    res = analyze_top_bucket(y_proba, returns)
    assert res["status"] == "computed"
    assert "top_10" in res
    assert res["top_10"]["count"] == 10


def test_regime_robustness() -> None:
    df = _mock_dataset()
    y_pred = np.random.choice([0, 1], size=len(df))
    y_true = df["target_up_after_cost_12bar"].values
    res = analyze_regime_robustness(df, y_pred, y_true)
    assert res["status"] == "computed"
    assert "by_year" in res
    assert "by_trend" in res
