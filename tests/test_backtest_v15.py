import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

from galapagos.agent.decision_context import build_decision_context
from galapagos.agent.decision_parser import parse_decision_response_with_metadata
from galapagos.agent.decision_prompt import build_llm_decision_prompt
from galapagos.agent.decision_schema import DecisionType
from galapagos.agent.decision_validator import validate_decision_context
from galapagos.agent.offline_llm_policy import generate_offline_llm_response
from galapagos.analysis.backtest_comparison import compare_backtest_profiles
from galapagos.analysis.backtest_metrics import calculate_backtest_metrics
from galapagos.analysis.policy_comparison import compare_policies
from galapagos.analysis.risk_rejection_analysis import analyze_risk_rejections
from galapagos.backtest.anti_leakage import (
    AntiLeakageError,
    assert_replay_window,
    assert_strictly_increasing_timestamps,
    check_timeframe_gaps,
)
from galapagos.backtest.historical_data import cache_kraken_ohlcv
from galapagos.backtest.mock_policy import decide_with_policy
from galapagos.backtest.replay_engine import ReplayEngine
from galapagos.backtest.timeframe_utils import candle_close_time, timeframe_to_timedelta
from galapagos.reports.backtest_report import generate_backtest_report
from galapagos.reports.llm_offline_decision_report import (
    analyze_llm_offline_decisions,
    write_llm_offline_decision_report,
)

_SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_SCRIPTS_DIR))
_BASELINE_SPEC = importlib.util.spec_from_file_location(
    "run_baseline_suite",
    _SCRIPTS_DIR / "run_baseline_suite.py",
)
assert _BASELINE_SPEC and _BASELINE_SPEC.loader
_BASELINE_MODULE = importlib.util.module_from_spec(_BASELINE_SPEC)
_BASELINE_SPEC.loader.exec_module(_BASELINE_MODULE)
write_baseline_report = _BASELINE_MODULE.write_baseline_report

_LLM_SUITE_SPEC = importlib.util.spec_from_file_location(
    "run_llm_offline_suite",
    _SCRIPTS_DIR / "run_llm_offline_suite.py",
)
assert _LLM_SUITE_SPEC and _LLM_SUITE_SPEC.loader
_LLM_SUITE_MODULE = importlib.util.module_from_spec(_LLM_SUITE_SPEC)
_LLM_SUITE_SPEC.loader.exec_module(_LLM_SUITE_MODULE)
_write_llm_suite_report = _LLM_SUITE_MODULE._write_report


class FakeCollector:
    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 250) -> pd.DataFrame:
        return sample_ohlcv(rows=min(limit, 80))


def sample_ohlcv(rows: int = 80) -> pd.DataFrame:
    data = []
    price = 100.0
    for index in range(rows):
        close = price + 0.5
        data.append(
            {
                "timestamp": pd.Timestamp("2026-01-01") + pd.Timedelta(minutes=30 * index),
                "open": price,
                "high": close + 1,
                "low": price - 1,
                "close": close,
                "volume": 100 + index,
            }
        )
        price = close
    return pd.DataFrame(data)


def profile() -> dict:
    return {
        "name": "galapagos_30m",
        "symbol": "BTC/USD",
        "timeframe": "30m",
        "paper_trading_only": True,
        "max_trades_per_day": 100,
        "max_position_duration_minutes": 240,
    }


def risk_config() -> dict:
    return {
        "simulated_initial_capital": 10_000,
        "max_risk_per_trade": 0.005,
        "max_daily_loss": 0.5,
        "max_weekly_loss": 0.8,
        "max_trades_per_day": 100,
        "stop_loss_required": True,
        "take_profit_or_time_exit_required": True,
        "kill_switch_enabled": False,
        "required_critical_data": ["price", "volatility"],
        "max_open_positions_global": 10,
        "max_open_positions_per_profile": 10,
        "allow_multiple_positions_same_asset": True,
        "max_total_exposure_fraction": 10.0,
    }


def policy_context(
    *,
    current_position: dict | None = None,
    sma_20: float = 105,
    sma_50: float = 100,
    rows: int = 60,
) -> dict:
    data = sample_ohlcv(rows).to_dict("records")
    return {
        "profile": profile(),
        "market": {"last_close": float(data[-1]["close"])},
        "indicators": {
            "sma_20": sma_20,
            "sma_50": sma_50,
            "market_regime": {"trend": "range", "volatility_regime": "normal"},
        },
        "portfolio": {
            "current_position": current_position,
            "open_positions": [current_position] if current_position else [],
            "timestamp": "2026-01-01T00:00:00",
            "bars_in_position": 3,
            "unrealized_pnl": 0.0,
        },
        "ohlcv_window": data,
        "recent_trades": [],
        "recent_decisions": [],
    }


def decision_context(current_position: dict | None = None):
    context = policy_context(current_position=current_position)
    return build_decision_context(
        profile=profile(),
        market={
            "last_close": context["market"]["last_close"],
            "last_volume": 100,
            "last_high": context["market"]["last_close"] + 1,
            "last_low": context["market"]["last_close"] - 1,
        },
        indicators=context["indicators"] | {"realized_volatility": 0.01},
        derivatives={"funding": {"status": "unavailable"}},
        scenarios=[{"strategy": "momentum", "side": "LONG", "confidence_hint": 0.8}],
        portfolio=context["portfolio"],
        risk_config=risk_config(),
        decision_timestamp="2026-01-01T00:00:00",
        data_mode="historical_replay",
        run_id="run",
        ohlcv_window=context["ohlcv_window"],
    )


def test_historical_data_cache_mock(tmp_path) -> None:
    result = cache_kraken_ohlcv(
        symbol="BTC/USD",
        timeframe="30m",
        days=3,
        output_root=tmp_path,
        collector=FakeCollector(),
    )
    assert result.data_path.exists()
    assert result.metadata_path.exists()
    assert result.metadata["rows"] > 0
    assert result.metadata["data_hash"]
    assert result.metadata["requested_days"] == 3
    assert result.metadata["effective_limit"] <= result.metadata["requested_limit"]
    assert result.metadata["approx_actual_days"] > 0
    assert result.metadata["timeframe_minutes"] == 30


def test_timeframe_utils() -> None:
    assert timeframe_to_timedelta("30m") == pd.Timedelta(minutes=30)
    assert timeframe_to_timedelta("4h") == pd.Timedelta(hours=4)
    assert candle_close_time(pd.Timestamp("2026-01-01 00:00:00"), "30m") == pd.Timestamp(
        "2026-01-01 00:30:00"
    )


def test_decision_context_json_hash_and_unavailable_features() -> None:
    ctx = decision_context({"side": "LONG", "entry_price": 100, "size": 1})
    payload = ctx.to_dict()
    assert json.loads(ctx.to_json())["context_hash"] == payload["context_hash"]
    assert payload["portfolio"]["has_open_position"] is True
    assert "funding" in payload["unavailable_features"]
    assert decision_context().to_dict()["context_hash"] == decision_context().to_dict()[
        "context_hash"
    ]


def test_llm_prompt_contains_constraints() -> None:
    prompt = build_llm_decision_prompt(decision_context())
    assert "paper trading only" in prompt
    assert "open position" in prompt
    assert "unavailable" in prompt
    assert "Expected JSON schema fields" in prompt


def test_offline_llm_raw_response_parses_and_validates() -> None:
    ctx = decision_context()
    response = generate_offline_llm_response("llm_offline_balanced", ctx)
    parsed = parse_decision_response_with_metadata(
        response.raw_response,
        "galapagos_30m",
        "BTC/USD",
        "30m",
    )
    validation = validate_decision_context(
        parsed.decision,
        profile=profile(),
        market={"last_close": ctx.market["current_price"]},
        derivatives={"funding": {"status": "unavailable"}},
        config={
            "context_validation": {
                "enabled": True,
                "max_entry_price_deviation_bps": 50,
                "unavailable_data_policy": "fallback_no_trade",
            }
        },
    )
    assert parsed.validity == "valid_schema"
    assert validation.decision.profile == "galapagos_30m"


def test_offline_conservative_trades_less_than_aggressive() -> None:
    contexts = [decision_context() for _ in range(10)]
    conservative = [
        parse_decision_response_with_metadata(
            generate_offline_llm_response("llm_offline_conservative", ctx).raw_response,
            "galapagos_30m",
            "BTC/USD",
            "30m",
        ).decision.decision
        for ctx in contexts
    ]
    aggressive = [
        parse_decision_response_with_metadata(
            generate_offline_llm_response("llm_offline_aggressive", ctx).raw_response,
            "galapagos_30m",
            "BTC/USD",
            "30m",
        ).decision.decision
        for ctx in contexts
    ]
    assert sum(item in {DecisionType.LONG, DecisionType.SHORT} for item in aggressive) >= sum(
        item in {DecisionType.LONG, DecisionType.SHORT} for item in conservative
    )


def test_offline_policy_no_new_entry_when_position_open() -> None:
    ctx = decision_context({"side": "LONG", "entry_price": 100, "size": 1})
    parsed = parse_decision_response_with_metadata(
        generate_offline_llm_response("llm_offline_aggressive", ctx).raw_response,
        "galapagos_30m",
        "BTC/USD",
        "30m",
    )
    assert parsed.decision.decision in {DecisionType.HOLD, DecisionType.CLOSE}


def test_anti_leakage_detects_unsorted_timestamps() -> None:
    df = sample_ohlcv(3)
    df.loc[2, "timestamp"] = df.loc[0, "timestamp"]
    with pytest.raises(AntiLeakageError):
        assert_strictly_increasing_timestamps(df)


def test_anti_leakage_detects_decision_at_open() -> None:
    window = sample_ohlcv(50).rename(columns={"timestamp": "candle_open_timestamp"})
    with pytest.raises(AntiLeakageError, match="before the visible candle close"):
        assert_replay_window(
            window,
            replay_index=49,
            decision_timestamp=window["candle_open_timestamp"].iloc[-1],
            timeframe="30m",
            warmup_bars=50,
        )


def test_anti_leakage_accepts_decision_at_close() -> None:
    window = sample_ohlcv(50).rename(columns={"timestamp": "candle_open_timestamp"})
    decision_timestamp = candle_close_time(window["candle_open_timestamp"].iloc[-1], "30m")
    check = assert_replay_window(
        window,
        replay_index=49,
        decision_timestamp=decision_timestamp,
        timeframe="30m",
        warmup_bars=50,
    )
    assert check.passed is True
    assert check.last_candle_close == decision_timestamp


def test_timeframe_gap_is_degraded() -> None:
    data = sample_ohlcv(5).rename(columns={"timestamp": "candle_open_timestamp"})
    data.loc[3, "candle_open_timestamp"] += pd.Timedelta(minutes=30)
    with pytest.warns(RuntimeWarning):
        status = check_timeframe_gaps(data, timeframe="30m")
    assert status["status"] == "degraded"


def test_simple_momentum_policy_produces_coherent_decision() -> None:
    decision = decide_with_policy(
        "simple_momentum",
        {
            "profile": profile(),
            "market": {"last_close": 110},
            "indicators": {
                "sma_20": 105,
                "sma_50": 100,
                "market_regime": {"volatility_regime": "normal"},
            },
        },
    )
    assert decision.decision == "LONG"


def test_state_aware_momentum_does_not_enter_when_position_open() -> None:
    decision = decide_with_policy(
        "state_aware_momentum",
        policy_context(
            current_position={"side": "LONG", "entry_price": 100, "size": 1},
            sma_20=105,
            sma_50=100,
        ),
    )
    assert decision.decision == DecisionType.HOLD


def test_state_aware_momentum_closes_on_invalidation() -> None:
    decision = decide_with_policy(
        "state_aware_momentum",
        policy_context(
            current_position={"side": "LONG", "entry_price": 100, "size": 1},
            sma_20=95,
            sma_50=100,
        ),
    )
    assert decision.decision == DecisionType.CLOSE


def test_state_aware_breakout_uses_visible_window_only() -> None:
    context = policy_context(rows=30)
    for row in context["ohlcv_window"][:-1]:
        row["high"] = 100
        row["low"] = 95
    context["ohlcv_window"][-1]["close"] = 102
    context["market"]["last_close"] = 102
    decision = decide_with_policy("state_aware_breakout", context)
    assert decision.decision == DecisionType.LONG


def test_state_aware_mean_reversion_uses_visible_window_only() -> None:
    context = policy_context(rows=30)
    for row in context["ohlcv_window"]:
        row["close"] = 100
    context["ohlcv_window"][-1]["close"] = 90
    context["market"]["last_close"] = 90
    decision = decide_with_policy("state_aware_mean_reversion", context)
    assert decision.decision == DecisionType.LONG


def test_replay_engine_does_not_see_future(tmp_path) -> None:
    data_path = tmp_path / "ohlcv.csv"
    sample_ohlcv(80).to_csv(data_path, index=False)
    result = ReplayEngine(
        profile=profile(),
        data_path=data_path,
        risk_config=risk_config(),
        initial_capital=10_000,
        policy="always_no_trade",
        warmup_bars=50,
    ).run()
    first_decision = result["decisions"][0]
    assert first_decision["replay_index"] == 49
    assert first_decision["decision_timestamp"] == first_decision["candle_close_timestamp"]
    assert first_decision["decision_timestamp"] > first_decision["candle_open_timestamp"]
    assert len(result["decisions"]) == 31


def test_force_close_at_end_closes_positions(tmp_path) -> None:
    data_path = tmp_path / "ohlcv.csv"
    sample_ohlcv(80).to_csv(data_path, index=False)
    result = ReplayEngine(
        profile=profile(),
        data_path=data_path,
        risk_config=risk_config(),
        initial_capital=10_000,
        policy="always_long",
        warmup_bars=50,
        force_close_at_end=True,
    ).run()
    assert result["open_positions"] == []
    assert any(trade["close_reason"] == "backtest_end" for trade in result["trades"])
    assert result["metrics"]["unrealized_pnl"] == 0.0


def test_backtest_metrics_calculated() -> None:
    metrics = calculate_backtest_metrics(
        trades=[
            {"status": "CLOSED", "pnl": 10, "fees": 1, "slippage": 0.5},
            {"status": "CLOSED", "pnl": -5, "fees": 1, "slippage": 0.5},
        ],
        decisions=[{"decision": "NO_TRADE", "risk_approved": True}],
        equity_curve=[{"equity": 100}, {"equity": 90}, {"equity": 110}],
        total_bars=3,
        open_positions=[],
        current_price=100,
    )
    assert metrics["closed_trades"] == 2
    assert metrics["profit_factor"] == 2
    assert metrics["max_drawdown"] == -0.1
    assert metrics["exposure_time"] <= 1.0
    assert "exposure_time_percent" in metrics


def test_exposure_time_none_half_full_and_capped() -> None:
    none = calculate_backtest_metrics(
        trades=[],
        decisions=[],
        equity_curve=[{"equity": 100, "open_position_count": 0} for _ in range(4)],
        total_bars=4,
        open_positions=[],
        current_price=100,
        backtest_days=1,
    )
    half = calculate_backtest_metrics(
        trades=[],
        decisions=[],
        equity_curve=[
            {"equity": 100, "open_position_count": 1},
            {"equity": 100, "open_position_count": 1},
            {"equity": 100, "open_position_count": 0},
            {"equity": 100, "open_position_count": 0},
        ],
        total_bars=2,
        open_positions=[],
        current_price=100,
        backtest_days=1,
    )
    full = calculate_backtest_metrics(
        trades=[],
        decisions=[],
        equity_curve=[{"equity": 100, "open_position_count": 3} for _ in range(4)],
        total_bars=1,
        open_positions=[],
        current_price=100,
        backtest_days=1,
    )
    assert none["exposure_time"] == 0.0
    assert half["exposure_time"] == 0.5
    assert full["exposure_time"] == 1.0
    assert full["exposure_time_percent"] == 100.0


def test_compare_backtest_profiles_uses_backtest_keys() -> None:
    comparison = compare_backtest_profiles(
        {
            "galapagos_30m": {
                "total_trades": 3,
                "closed_trades": 2,
                "realized_pnl": 10,
                "unrealized_pnl": 1,
                "total_fees": 2,
                "total_slippage": 1,
                "max_drawdown": -0.1,
                "profit_factor": 2,
                "expectancy": 5,
                "average_win": 8,
                "average_loss": -3,
                "exposure_time": 0.4,
                "backtest_days": 10,
                "realized_pnl_per_day": 1,
                "fees_per_day": 0.2,
                "slippage_per_day": 0.1,
                "trades_per_day": 0.3,
                "risk_rejected_per_day": 0.1,
                "no_trade_per_day": 0.7,
                "no_trade_count": 7,
                "risk_rejected_count": 1,
            },
            "galapagos_4h": {
                "total_trades": 1,
                "closed_trades": 1,
                "realized_pnl": 4,
                "unrealized_pnl": 0,
                "total_fees": 1,
                "total_slippage": 0.5,
                "max_drawdown": -0.05,
                "profit_factor": 1.2,
                "expectancy": 4,
                "average_win": 4,
                "average_loss": 0,
                "exposure_time": 0.2,
                "backtest_days": 10,
                "realized_pnl_per_day": 0.4,
                "fees_per_day": 0.1,
                "slippage_per_day": 0.05,
                "trades_per_day": 0.1,
                "risk_rejected_per_day": 0,
                "no_trade_per_day": 0.9,
                "no_trade_count": 9,
                "risk_rejected_count": 0,
            },
        }
    )
    assert comparison["profiles"]["galapagos_30m"]["closed_trades"] == 2
    assert comparison["deltas"]["realized_pnl_delta_30m_minus_4h"] == 6
    assert comparison["deltas"]["total_trades_delta_30m_minus_4h"] == 2
    assert comparison["deltas"]["realized_pnl_per_day_delta_30m_minus_4h"] == 0.6
    assert comparison["period_equivalence"]["equivalent"] is True


def test_policy_comparison_outputs_expected_metrics() -> None:
    rows = compare_policies(
        [
            {
                "policy": "state_aware_momentum",
                "metrics": {
                    "galapagos_30m": {
                        "backtest_days": 10,
                        "total_trades": 2,
                        "trades_per_day": 0.2,
                        "realized_pnl": -1,
                        "realized_pnl_per_day": -0.1,
                        "max_drawdown": -0.01,
                        "profit_factor": 0.8,
                        "expectancy": -0.5,
                        "fees_per_day": 0.1,
                        "slippage_per_day": 0.2,
                        "risk_rejected_per_day": 0.0,
                        "no_trade_per_day": 3,
                        "exposure_time": 0.5,
                        "average_trade_duration_minutes": 120,
                    }
                },
            }
        ]
    )
    assert rows[0]["policy_name"] == "state_aware_momentum"
    assert rows[0]["profile"] == "galapagos_30m"
    assert rows[0]["average_trade_duration_minutes"] == 120


def test_risk_rejection_analysis_counts_reasons() -> None:
    analysis = analyze_risk_rejections(
        [
            {
                "run_id": "run",
                "raw_results": {
                    "galapagos_30m": {
                        "decisions": [
                            {
                                "profile": "galapagos_30m",
                                "strategy": "momentum",
                                "decision": "LONG",
                                "risk_approved": False,
                                "risk_reasons": ["Max total exposure fraction exceeded"],
                            }
                        ]
                    }
                },
            }
        ]
    )
    assert analysis["total_rejections"] == 1
    assert analysis["rejections_by_profile"]["galapagos_30m"] == 1
    assert analysis["rejections_by_reason"]["Max total exposure fraction exceeded"] == 1


def test_run_backtest_generates_report(tmp_path) -> None:
    data_path = tmp_path / "ohlcv.csv"
    sample_ohlcv(80).to_csv(data_path, index=False)
    result = ReplayEngine(
        profile=profile(),
        data_path=data_path,
        risk_config=risk_config(),
        initial_capital=10_000,
        policy="always_no_trade",
        warmup_bars=50,
    ).run()
    payload = {
        "run_id": result["run_id"],
        "config": {"test": True},
        "period": {"galapagos_30m": result["period"]},
        "data_source": "test",
        "data_hashes": {"galapagos_30m": "hash"},
        "profiles": ["galapagos_30m"],
        "policy": "always_no_trade",
        "metrics": {"galapagos_30m": result["metrics"]},
        "comparison": {},
    }
    paths = generate_backtest_report(payload, tmp_path)
    assert paths["markdown"].exists()
    assert json.loads(paths["json"].read_text(encoding="utf-8"))["run_id"] == result["run_id"]


def test_replay_supports_llm_offline_policy(tmp_path) -> None:
    data_path = tmp_path / "ohlcv.csv"
    sample_ohlcv(80).to_csv(data_path, index=False)
    result = ReplayEngine(
        profile=profile(),
        data_path=data_path,
        risk_config=risk_config(),
        initial_capital=10_000,
        policy="llm_offline_aggressive",
        warmup_bars=50,
        force_close_at_end=True,
    ).run()
    assert result["decisions"]
    assert "raw_response" in result["decisions"][0]
    assert "context_hash" in result["decisions"][0]


def test_run_baseline_suite_report_writer_generates_report(tmp_path) -> None:
    report = {
        "generated_at_utc": "2026-01-01T00:00:00+00:00",
        "metadata": {},
        "policy_comparison": [],
        "answers": {
            "least_losing_policy": {},
            "lowest_risk_reject_policy": {},
            "state_aware_reduces_rejects": True,
        },
    }
    paths = write_baseline_report(report, tmp_path)
    assert paths["markdown"].exists()
    assert paths["json"].exists()


def test_run_llm_offline_suite_report_writer_generates_report(tmp_path) -> None:
    report = {
        "generated_at_utc": "2026-01-01T00:00:00+00:00",
        "policy_comparison": [],
        "answers": {"rankings": {}},
        "llm_offline_decision_analysis": {"decision_distribution_by_policy": {}},
    }
    paths = _write_llm_suite_report(report, tmp_path)
    assert paths["markdown"].exists()
    assert paths["json"].exists()


def test_llm_offline_decision_report_generates(tmp_path) -> None:
    analysis = analyze_llm_offline_decisions(
        [
            {
                "policy": "llm_offline_balanced",
                "raw_results": {
                    "galapagos_30m": {
                        "decisions": [
                            {
                                "decision": "NO_TRADE",
                                "raw_response": json.dumps(
                                    {
                                        "decision": "NO_TRADE",
                                        "confidence": 0.5,
                                        "risk_fraction": 0.0,
                                        "strategy": "no_trade",
                                    }
                                ),
                                "risk_approved": True,
                                "context_hash": "ctx",
                                "prompt_hash": "prompt",
                            }
                        ]
                    }
                },
            }
        ]
    )
    paths = write_llm_offline_decision_report(analysis, tmp_path)
    assert paths["markdown"].exists()
    assert paths["json"].exists()
