from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from galapagos.data.derivatives_readiness import ReadinessStatus, build_derivatives_readiness
from galapagos.evaluation.batch_runner import (
    load_checkpoint,
    resume_run,
    save_checkpoint,
    stop_gracefully_on_quota_error,
)
from galapagos.research.benchmark import run_benchmarks
from galapagos.research.bootstrap import (
    bootstrap_trade_pnl,
    permutation_test_signal_vs_random,
)
from galapagos.research.cost_analysis import analyze_costs
from galapagos.research.labeling import (
    compute_forward_returns,
    compute_mfe_mae,
    compute_tp_sl_first_label,
)
from galapagos.research.random_baselines import generate_random_entries_same_count
from galapagos.research.regime_splits import classify_regime_window
from galapagos.research.signal_quality import analyze_signal_quality


def _ohlcv(closes: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=len(closes), freq="4h"),
            "open": closes,
            "high": [value * 1.02 for value in closes],
            "low": [value * 0.98 for value in closes],
            "close": closes,
            "volume": [100.0] * len(closes),
        }
    )


def test_forward_returns_and_missing_tail() -> None:
    data = _ohlcv([100, 110, 121, 100])
    labeled = compute_forward_returns(data, horizons=[1, 3])
    assert labeled["forward_return_1bar"].iloc[0] == pytest.approx(0.10)
    assert labeled["forward_return_3bar"].iloc[0] == pytest.approx(0.0)
    assert pd.isna(labeled["forward_return_3bar"].iloc[2])


def test_mfe_mae_and_tp_sl_conservative() -> None:
    data = _ohlcv([100, 100, 100, 100])
    labeled = compute_mfe_mae(data, horizons=[3])
    assert labeled["max_favorable_excursion_3bar"].iloc[0] == pytest.approx(0.02)
    assert labeled["max_adverse_excursion_3bar"].iloc[0] == pytest.approx(-0.02)
    tp_sl = compute_tp_sl_first_label(data, tp_pct=0.01, sl_pct=0.01, horizon_bars=3)
    assert tp_sl["tp_before_sl_conservative"].iloc[0] is False
    assert pd.isna(tp_sl["tp_before_sl_conservative"].iloc[-1])


def test_random_baseline_and_bootstrap_reproducible() -> None:
    data = _ohlcv([100, 101, 102, 103, 104])
    first = generate_random_entries_same_count(data, 3, seed=7)
    second = generate_random_entries_same_count(data, 3, seed=7)
    assert first["timestamp"].tolist() == second["timestamp"].tolist()
    boot = bootstrap_trade_pnl([{"net_pnl": 1.0}, {"net_pnl": -0.5}], n_bootstrap=20, seed=1)
    assert len(boot["samples"]) == 20
    test = permutation_test_signal_vs_random([1.0, 2.0], [0.0, 0.5], n_permutations=20, seed=1)
    assert 0.0 <= test["p_value"] <= 1.0


def test_benchmarks_costs_regimes_and_signal_quality() -> None:
    data = _ohlcv([100, 101, 102, 103, 104, 105, 106, 107])
    benchmarks = run_benchmarks(data)
    assert benchmarks["cash"]["return"] == 0.0
    assert benchmarks["buy_and_hold"]["return"] > 0
    costs = analyze_costs(
        [
            {"gross_pnl": 1.0, "fees": 0.6, "slippage": 0.5, "net_pnl": -0.1},
            {"gross_pnl": -1.0, "fees": 0.2, "slippage": 0.3, "net_pnl": -1.5},
        ]
    )
    assert costs["positive_gross_destroyed_count"] == 1
    assert classify_regime_window(data)["regime_label"] in {"uptrend", "range"}
    signals = pd.DataFrame({"index": [0, 1], "group": ["LONG candidates", "NO_TRADE"]})
    labels = compute_forward_returns(data, horizons=[1, 3, 6, 12])
    quality = analyze_signal_quality(labels, signals, random_returns=[0.0, 0.01])
    assert "sample_below_30" in quality["warnings"]


def test_derivatives_readiness_does_not_log_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COINGLASS_API_KEY", "secret-value")
    payload = build_derivatives_readiness("BTCUSDT", dry_run=True)
    encoded = json.dumps(payload)
    assert "secret-value" not in encoded
    assert any(check["status"] == ReadinessStatus.AVAILABLE.value for check in payload["checks"])


def test_batch_checkpoint_resume(tmp_path: Path) -> None:
    path = save_checkpoint(
        "run-1",
        [{"id": 1}],
        [{"id": 2}],
        [],
        checkpoint_dir=tmp_path,
    )
    assert path.exists()
    checkpoint = load_checkpoint("run-1", checkpoint_dir=tmp_path)
    assert checkpoint["completed_items"] == [{"id": 1}]
    resumed = resume_run("run-1", checkpoint_dir=tmp_path)
    assert resumed["pending_items"] == [{"id": 2}]
    stopped = stop_gracefully_on_quota_error(
        "run-2",
        [],
        [{"id": 3}],
        [{"id": "failure"}],
        checkpoint_dir=tmp_path,
    )
    assert stopped["status"] == "quota_limited"
