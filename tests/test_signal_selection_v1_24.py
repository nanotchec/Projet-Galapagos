from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd

from galapagos.research.signal_selection.candidate_features import (
    build_signal_selection_features,
)
from galapagos.research.signal_selection.filter_sweep import run_filter_sweep
from galapagos.research.signal_selection.frequency_analysis import analyze_frequency
from galapagos.research.signal_selection.random_baselines import random_same_count_baseline
from galapagos.research.signal_selection.recommendation_engine import (
    build_selection_recommendation,
)
from galapagos.research.signal_selection.selection_rules import build_default_rules
from galapagos.research.trade_ledger.schema import (
    TradeCandidate,
    TradeSide,
    TradeSimulationResult,
)


def _mock_features() -> pd.DataFrame:
    timestamps = pd.date_range("2024-01-01", periods=40, freq="4h", tz="UTC")
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "policy": ["horizon_only"] * 40,
            "predicted_probability": [0.50 + i / 200 for i in range(40)],
            "gross_expected_move_pct": [0.001 + i / 10000 for i in range(40)],
            "mfe_proxy_pct": [0.002 + i / 10000 for i in range(40)],
            "cost_pct": [0.003] * 40,
            "gross_pnl_pct": [0.002 if i % 2 else -0.001 for i in range(40)],
            "net_pnl_pct": [0.001 if i % 2 else -0.004 for i in range(40)],
            "volatility_regime": ["normal"] * 30 + ["high"] * 10,
            "trend_regime": ["bull"] * 20 + ["bear"] * 20,
            "is_cost_viable": [i > 20 for i in range(40)],
        }
    )


def test_feature_builder_handles_missing_probability() -> None:
    ts = datetime(2024, 1, 1, tzinfo=UTC)
    candidate = TradeCandidate(
        candidate_id="c1",
        signal_time=ts,
        entry_time=ts + timedelta(hours=4),
        side=TradeSide.LONG,
        entry_price=100.0,
        max_holding_bars=6,
        max_holding_time=ts + timedelta(hours=28),
        source="mock",
        source_version="test",
        policy_name="horizon_only",
        policy_version="test",
    )
    result = TradeSimulationResult(
        candidate_id="c1",
        signal_time=ts,
        entry_time=ts + timedelta(hours=4),
        side=TradeSide.LONG,
        entry_price=100.0,
        exit_price=101.0,
        exit_time=ts + timedelta(hours=28),
        exit_reason="horizon_timeout",
        pnl_pct=0.01,
        cost_proxy_pct=0.003,
        pnl_after_cost_pct=0.007,
        mfe_pct=0.012,
        mae_pct=-0.004,
        bars_held_intrabar=72,
        used_intrabar=True,
        coverage_pct=1.0,
        simulation_status="complete",
    )
    dataset = pd.DataFrame(
        {
            "timestamp": [ts, ts + timedelta(hours=4)],
            "open": [100, 100],
            "high": [101, 102],
            "low": [99, 99],
            "close": [100, 101],
            "max_favorable_excursion_6bar": [0.01, 0.02],
        }
    )
    features, audit = build_signal_selection_features(
        signals_df=pd.DataFrame({"timestamp": [ts]}),
        dataset=dataset,
        reconstructed={"horizon_only": {"candidates": [candidate], "results": [result]}},
    )
    assert len(features) == 1
    assert "predicted_probability" in features
    assert audit["rows"] == 1


def test_selection_rules_return_expected_subset() -> None:
    frame = _mock_features()
    rules = {rule.name: rule for rule in build_default_rules()}
    selected = frame[rules["prob_ge_0_65"].apply(frame)]
    assert len(selected) == 10
    assert rules["no_trade"].apply(frame).sum() == 0


def test_random_same_count_baseline_reproducible() -> None:
    frame = _mock_features()
    first = random_same_count_baseline(frame, 10, iterations=50, seed=42)
    second = random_same_count_baseline(frame, 10, iterations=50, seed=42)
    assert first["random_mean"] == second["random_mean"]
    assert first["random_p95"] == second["random_p95"]


def test_filter_sweep_marks_small_sample() -> None:
    frame = _mock_features().head(20)
    rules = [rule for rule in build_default_rules() if rule.name == "top_10pct_probability"]
    sweep, _ = run_filter_sweep(frame, rules, policies=["horizon_only"], iterations=20)
    assert "SAMPLE_TOO_SMALL" in sweep[0]["verdict"]


def test_frequency_filter_selects_one_per_day() -> None:
    analysis = analyze_frequency(_mock_features())
    row = next(item for item in analysis["rows"] if item["rule_name"] == "highest_score_per_day")
    assert row["selected_count"] == 7


def test_recommendation_keeps_reviewer_disabled() -> None:
    recommendation = build_selection_recommendation(
        sweep=[
            {
                "rule_name": "all_candidates",
                "policy": "horizon_only",
                "selected_count": 40,
                "net_mean_pnl_pct": -0.001,
                "beats_random_p95": False,
                "verdict": ["FILTER_FAILS_AFTER_COSTS"],
            }
        ],
        confidence_verdicts=["CONFIDENCE_SIGNAL_WEAK"],
        regime_verdicts=["NO_REGIME_SELECTION_EDGE"],
        frequency_verdicts=["NO_FREQUENCY_EDGE"],
    )
    assert recommendation["ready_for_reviewer"] is False
    assert recommendation["holdout_executed"] is False
    assert recommendation["no_real_trading"] is True


def test_no_codex_or_holdout_in_signal_selection_script() -> None:
    text = Path("scripts/run_cost_aware_signal_selection.py").read_text(encoding="utf-8")
    assert "allow-codex-cli" not in text
    assert "subprocess" not in text
    assert "holdout_executed\": False" in text
