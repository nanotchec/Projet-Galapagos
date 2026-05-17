from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd

from galapagos.research.signal_selection.candidate_features import (
    build_signal_selection_features,
)
from galapagos.research.signal_selection.evaluation import evaluate_rule_subset
from galapagos.research.signal_selection.leakage_audit import (
    audit_signal_selection_leakage,
    classify_column,
)
from galapagos.research.signal_selection.selection_rules import build_default_rules
from galapagos.research.signal_selection.walk_forward_validation import (
    run_walk_forward_validation,
)
from galapagos.research.trade_ledger.schema import (
    TradeCandidate,
    TradeSide,
    TradeSimulationResult,
)


def test_leakage_audit_flags_forward_returns_as_forbidden_future() -> None:
    assert classify_column("forward_return_6bar") == "forbidden_future"
    assert classify_column("gross_pnl_pct") == "realized_outcome"
    audit = audit_signal_selection_leakage(
        features=pd.DataFrame(columns=["forward_return_6bar", "gross_pnl_pct"]),
        rules=build_default_rules(),
    )
    assert "forward_return_6bar" in audit["forbidden_future_columns"]
    assert audit["causal_subset_available"] is True


def test_candidate_features_separate_causal_and_diagnostic_forward_moves() -> None:
    ts = datetime(2024, 1, 1, tzinfo=UTC)
    candidates = []
    results = []
    signal_rows = []
    for idx, forward_return in enumerate([0.01, 0.50]):
        signal_time = ts + timedelta(hours=idx * 4)
        candidate_id = f"c{idx}"
        candidates.append(
            TradeCandidate(
                candidate_id=candidate_id,
                signal_time=signal_time,
                entry_time=signal_time + timedelta(hours=4),
                side=TradeSide.LONG,
                entry_price=100.0,
                max_holding_bars=6,
                max_holding_time=signal_time + timedelta(hours=28),
                source="mock",
                source_version="test",
                policy_name="horizon_only",
                policy_version="test",
            )
        )
        results.append(
            TradeSimulationResult(
                candidate_id=candidate_id,
                signal_time=signal_time,
                entry_time=signal_time + timedelta(hours=4),
                side=TradeSide.LONG,
                entry_price=100.0,
                exit_price=101.0,
                exit_time=signal_time + timedelta(hours=28),
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
        )
        signal_rows.append(
            {
                "timestamp": signal_time,
                "predicted_probability": 0.60,
                "forward_return_6bar": forward_return,
                "forward_return_12bar": forward_return,
            }
        )
    dataset = pd.DataFrame(
        {
            "timestamp": pd.date_range(ts, periods=40, freq="4h", tz="UTC"),
            "open": range(40),
            "high": range(1, 41),
            "low": range(40),
            "close": [100 + i for i in range(40)],
            "max_favorable_excursion_6bar": [0.02] * 40,
        }
    )
    features, audit = build_signal_selection_features(
        signals_df=pd.DataFrame(signal_rows),
        dataset=dataset,
        reconstructed={"horizon_only": {"candidates": candidates, "results": results}},
    )
    assert features["diagnostic_forward_move_pct"].iloc[0] != features[
        "diagnostic_forward_move_pct"
    ].iloc[1]
    assert features["causal_expected_move_pct"].iloc[0] == features[
        "causal_expected_move_pct"
    ].iloc[1]
    assert features["gross_expected_move_pct"].equals(features["causal_expected_move_pct"])
    assert "diagnostic_forward_move_pct" in audit["diagnostic_only_columns"]


def test_low_frequency_strict_score_is_causal() -> None:
    rule = next(rule for rule in build_default_rules() if rule.name == "low_frequency_strict_score")
    assert rule.causal is True
    assert set(rule.used_columns) == {"timestamp", "predicted_probability"}


def test_beats_random_p95_verdict_is_explicit() -> None:
    frame = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=40, freq="4h", tz="UTC"),
            "gross_pnl_pct": [0.02] * 40,
            "net_pnl_pct": [0.01] * 40,
            "cost_pct": [0.003] * 40,
        }
    )
    metrics = evaluate_rule_subset(
        frame,
        frame,
        rule_name="mock",
        policy="horizon_only",
        random_stats={"random_mean": 0.0, "random_p95": 0.005},
    )
    assert metrics["beats_random_p95"] is True
    assert "BEATS_RANDOM_P95_PROMISING_BUT_UNVALIDATED" in metrics["verdict"]


def test_walk_forward_report_contains_all_windows() -> None:
    timestamps = pd.date_range("2024-01-01", "2026-05-01", freq="4h", tz="UTC")
    frame = pd.DataFrame(
        {
            "timestamp": timestamps,
            "policy": "horizon_only",
            "predicted_probability": [0.50 + (i % 20) / 100 for i in range(len(timestamps))],
            "gross_pnl_pct": [0.004 if i % 3 else -0.002 for i in range(len(timestamps))],
            "net_pnl_pct": [0.001 if i % 3 else -0.005 for i in range(len(timestamps))],
            "cost_pct": 0.003,
        }
    )
    payload = run_walk_forward_validation(frame, iterations=10)
    assert payload["windows"] == ["2024_H1", "2024_H2", "2025_H1", "2025_H2", "2026_YTD"]
    primary_rows = [
        row
        for row in payload["rows"]
        if row["rule_name"] == "low_frequency_strict_score"
        and row["policy"] == "horizon_only"
    ]
    assert len(primary_rows) == 5


def test_no_codex_holdout_or_real_trading_in_v1_24_1_scripts() -> None:
    for path in [
        Path("scripts/audit_signal_selection_leakage.py"),
        Path("scripts/run_signal_selection_walk_forward.py"),
    ]:
        text = path.read_text(encoding="utf-8")
        assert "allow-codex-cli" not in text
        assert "subprocess" not in text
        assert "holdout_executed" in text
        assert "no_real_trading" in text
