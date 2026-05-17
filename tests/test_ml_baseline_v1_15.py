"""Tests for ML baseline lab V1.15."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from galapagos.research.ml.calibration import calibration_analysis
from galapagos.research.ml.feature_importance import extract_feature_importance
from galapagos.research.ml.feature_sets import (
    FEATURE_SETS,
    build_ohlcv_basic_features,
    get_feature_set,
    is_forbidden,
)
from galapagos.research.ml.metrics import classification_metrics, regression_metrics
from galapagos.research.ml.models import (
    MODEL_REGISTRY,
    SKLEARN_AVAILABLE,
    FallbackDummyModel,
    create_model,
)
from galapagos.research.ml.report import build_ml_summary, ml_verdict
from galapagos.research.ml.targets import (
    ALL_TARGET_COLUMNS,
    build_ml_targets,
    target_report,
)
from galapagos.research.ml.walk_forward import (
    build_default_windows,
    run_walk_forward,
)


def _mock_dataset(n: int = 500) -> pd.DataFrame:
    """Create a minimal mock dataset for testing."""
    rng = np.random.RandomState(42)
    close = 100.0 + np.cumsum(rng.randn(n) * 0.5)
    return pd.DataFrame({
        "timestamp": pd.date_range("2022-01-01", periods=n, freq="4h", tz="UTC"),
        "open": close - rng.rand(n) * 0.3,
        "high": close + rng.rand(n) * 0.5,
        "low": close - rng.rand(n) * 0.5,
        "close": close,
        "volume": rng.rand(n) * 1000 + 100,
    })


# --- Target tests ---

def test_targets_built_correctly() -> None:
    df = _mock_dataset(200)
    result = build_ml_targets(df)
    for col in ALL_TARGET_COLUMNS:
        assert col in result.columns, f"Missing target: {col}"
    # Last rows should be NaN for forward targets
    assert pd.isna(result["target_return_12bar"].iloc[-1])
    assert pd.isna(result["target_return_6bar"].iloc[-1])


def test_targets_last_rows_nan() -> None:
    df = _mock_dataset(100)
    result = build_ml_targets(df)
    # For 12-bar horizon, last 12 rows should be NaN
    assert result["target_return_12bar"].iloc[-12:].isna().all()


def test_target_not_used_as_feature() -> None:
    for col in ALL_TARGET_COLUMNS:
        assert is_forbidden(col), f"Target {col} should be forbidden as feature"


def test_target_report() -> None:
    df = _mock_dataset(200)
    result = build_ml_targets(df)
    report = target_report(result)
    assert "targets" in report
    assert len(report["targets"]) > 0


# --- Feature set tests ---

def test_feature_sets_exclude_targets() -> None:
    for name, cols in FEATURE_SETS.items():
        for col in cols:
            assert not is_forbidden(col), f"Feature {col} in set {name} is forbidden"


def test_forbidden_columns() -> None:
    assert is_forbidden("forward_return_6bar")
    assert is_forbidden("target_return_3bar")
    assert is_forbidden("timestamp")
    assert not is_forbidden("return_lag_1")
    assert not is_forbidden("realized_vol_12")


def test_ohlcv_basic_features_built() -> None:
    df = _mock_dataset(200)
    result = build_ohlcv_basic_features(df)
    assert "return_lag_1" in result.columns
    assert "realized_vol_12" in result.columns
    assert "atr_14" in result.columns
    assert "volume_zscore" in result.columns


def test_get_feature_set_stable() -> None:
    df = _mock_dataset(200)
    df = build_ohlcv_basic_features(df)
    cols, report = get_feature_set(df, "ohlcv_basic")
    assert len(cols) > 0
    assert report["feature_set"] == "ohlcv_basic"
    assert report["forbidden_found"] == []


# --- Model tests ---

def test_fallback_dummy_model() -> None:
    model = FallbackDummyModel()
    x = np.random.randn(50, 3)
    y = np.array([0] * 30 + [1] * 20, dtype=float)
    model.fit(x, y)
    preds = model.predict(x)
    assert len(preds) == 50
    proba = model.predict_proba(x)
    assert proba.shape == (50, 2)


def test_sklearn_model_creation() -> None:
    if not SKLEARN_AVAILABLE:
        pytest.skip("sklearn not available")
    model = create_model("logistic_regression")
    assert model is not None


def test_dummy_model_always_available() -> None:
    # At least one model must always be available
    assert len(MODEL_REGISTRY) > 0


# --- Walk-forward tests ---

def test_walk_forward_chronological() -> None:
    windows = build_default_windows(2000, embargo_bars=6)
    for w in windows:
        assert w.train_start < w.train_end
        assert w.test_start < w.test_end
        assert w.train_end <= w.test_start, "No overlap allowed"


def test_walk_forward_no_overlap() -> None:
    windows = build_default_windows(5000, embargo_bars=6)
    for w in windows:
        assert w.train_end + 6 <= w.test_start


def test_walk_forward_embargo() -> None:
    windows = build_default_windows(5000, embargo_bars=10)
    for w in windows:
        assert w.test_start >= w.train_end + 10


def test_walk_forward_insufficient_data() -> None:
    windows = build_default_windows(50)
    assert len(windows) == 0


def test_run_walk_forward_on_mock() -> None:
    if not SKLEARN_AVAILABLE:
        pytest.skip("sklearn not available")
    df = _mock_dataset(800)
    df = build_ohlcv_basic_features(df)
    df = build_ml_targets(df)
    result = run_walk_forward(
        df,
        target_col="target_up_after_cost_6bar",
        feature_set_name="ohlcv_basic",
        model_name="logistic_regression",
        min_train_rows=50,
        min_test_rows=20,
    )
    assert result["status"] == "completed"


# --- Metrics tests ---

def test_classification_metrics_mock() -> None:
    y_true = np.array([1, 0, 1, 1, 0, 0, 1, 0, 1, 0] * 10, dtype=float)
    y_pred = np.array([1, 0, 0, 1, 0, 1, 1, 0, 1, 0] * 10, dtype=float)
    m = classification_metrics(y_true, y_pred)
    assert "accuracy" in m
    assert "base_rate" in m
    assert 0 <= m["accuracy"] <= 1


def test_regression_metrics_mock() -> None:
    y_true = np.random.randn(100)
    y_pred = y_true + np.random.randn(100) * 0.1
    m = regression_metrics(y_true, y_pred)
    assert "r2" in m
    assert m["r2"] > 0.5


def test_low_sample_warning() -> None:
    y_true = np.array([1, 0, 1], dtype=float)
    y_pred = np.array([1, 0, 0], dtype=float)
    m = classification_metrics(y_true, y_pred)
    assert "sample_below_30" in m["warnings"]


# --- Calibration tests ---

def test_calibration_bins() -> None:
    y_true = np.array([1, 0, 1, 1, 0, 0, 1, 0, 1, 0] * 5, dtype=float)
    y_proba = np.array([0.8, 0.2, 0.7, 0.9, 0.3, 0.4, 0.6, 0.1, 0.85, 0.15] * 5)
    cal = calibration_analysis(y_true, y_proba, n_bins=5)
    assert cal["status"] == "computed"
    assert "brier_score" in cal
    assert len(cal["bins"]) == 5


# --- Feature importance tests ---

def test_feature_importance_sklearn() -> None:
    if not SKLEARN_AVAILABLE:
        pytest.skip("sklearn not available")
    from sklearn.ensemble import RandomForestClassifier
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    x = np.random.randn(100, 5)
    y = (x[:, 0] > 0).astype(float)
    model.fit(x, y)
    result = extract_feature_importance(model, ["f0", "f1", "f2", "f3", "f4"])
    assert result["status"] == "computed"
    assert len(result["top_features"]) == 5


def test_feature_importance_unsupported() -> None:
    result = extract_feature_importance(object(), ["f0"])
    assert result["status"] == "not_supported"


# --- Report / verdict tests ---

def test_verdict_no_edge() -> None:
    assert ml_verdict([]) == "ML_NEEDS_MORE_DATA"
    assert ml_verdict([{"windows": [{"metrics": {"beats_random": False}}]}]) == "ML_NO_EDGE"


def test_verdict_beats_random() -> None:
    r = [{"windows": [{"metrics": {"beats_random": True}}]}]
    assert ml_verdict(r) == "ML_BEATS_RANDOM_BUT_NOT_COSTS"


def test_summary_structure() -> None:
    s = build_ml_summary([], sklearn_available=True, dataset_report={"rows": 100})
    assert s["version"] == "V1.15"
    assert s["holdout_executed"] is False
    assert s["codex_cli_called"] is False
    assert s["real_orders_possible"] is False


# --- Safety tests ---

def test_no_codex_cli_in_ml_package() -> None:
    """No Codex CLI invocations in the ML package."""
    import galapagos.research.ml as ml_pkg
    source_dir = Path(ml_pkg.__file__).parent
    forbidden = ["run_codex", "allow_codex_cli", "codex exec", "codex_cli("]
    for py_file in source_dir.glob("*.py"):
        content = py_file.read_text()
        for pattern in forbidden:
            assert pattern not in content, f"Found '{pattern}' in {py_file.name}"


def test_no_holdout_execution() -> None:
    """Walk-forward windows must not use holdout."""
    windows = build_default_windows(9000)
    for w in windows:
        assert "holdout" not in w.name.lower()


def test_no_real_trading() -> None:
    """Summary must declare no real orders."""
    s = build_ml_summary([], sklearn_available=True, dataset_report={})
    assert s["real_orders_possible"] is False


