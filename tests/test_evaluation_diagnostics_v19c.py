from __future__ import annotations

import json
from pathlib import Path

from galapagos.analysis.evaluation_diagnostics import (
    analyze_evaluation_diagnostics,
    cost_analysis,
    regime_analysis,
    side_analysis,
    simulate_hypothetical_filters,
)


def test_cost_analysis_calculates_ratios() -> None:
    trades = [
        _trade("LONG", 100, 80, fees=10, slippage=10),
        _trade("SHORT", -20, -35, fees=5, slippage=10),
    ]
    result = cost_analysis(trades)
    assert result["gross_pnl"] == 80
    assert result["net_pnl"] == 45
    assert result["total_costs"] == 35
    assert result["cost_to_gross_ratio"] == 35 / 80
    assert result["positive_gross_destroyed_count"] == 0


def test_side_analysis() -> None:
    result = side_analysis([_trade("LONG", 20, 10), _trade("SHORT", -5, -10)])
    assert result["LONG"]["trade_count"] == 1
    assert result["SHORT"]["net_pnl"] == -10


def test_missing_regime_data_handled() -> None:
    result = regime_analysis([{"net_pnl": 1, "gross_pnl": 2, "decision": "LONG"}])
    assert result["status"] == "regime data insufficient"


def test_filter_simulation() -> None:
    trades = [
        _trade("LONG", 20, 10, trend_long="up"),
        _trade("SHORT", -5, -10, trend_long="up"),
    ]
    result = simulate_hypothetical_filters(trades)
    assert result["exclude_short"]["trade_count"] == 1
    assert result["side_aligned_with_trend_long"]["net_pnl"] == 10


def test_diagnostics_loads_multiple_mock_ledgers(tmp_path: Path) -> None:
    calibration = tmp_path / "cal"
    validation = tmp_path / "val"
    calibration.mkdir()
    validation.mkdir()
    _write_report(
        calibration / "calibration_setup_review.json", "calibration", [_ledger("LONG", 5)]
    )
    _write_report(
        validation / "validation_1_setup_review.json", "validation_1", [_ledger("SHORT", -3)]
    )
    _write_report(
        validation / "validation_2_setup_review.json", "validation_2", [_ledger("LONG", 7)]
    )
    result = analyze_evaluation_diagnostics(
        include_calibration=True,
        include_validation=True,
        calibration_dir=calibration,
        validation_dir=validation,
    )
    assert len(result["windows"]) == 3
    assert result["global"]["trades"]["trade_count"] == 3
    assert result["holdout_executed"] is False


def _trade(
    side: str,
    gross: float,
    net: float,
    *,
    fees: float = 1.0,
    slippage: float = 1.0,
    trend_long: str = "down",
) -> dict:
    return {
        "decision": side,
        "gross_pnl": gross,
        "net_pnl": net,
        "fees": fees,
        "slippage": slippage,
        "setup_quality": "acceptable",
        "setup_quality_score": 0.6,
        "confidence": 0.6,
        "risk_reward_ratio": 2.0,
        "market_regime": {"trend": "uptrend"},
        "trend_long": trend_long,
        "trend_short": trend_long,
        "volatility": 0.01,
        "close_reason": "take_profit" if net > 0 else "stop_loss",
        "duration_hours": 4,
        "estimated_cost_impact": 0.1,
        "window": "mock",
    }


def _ledger(side: str, net: float) -> dict:
    gross = net + 1.0
    return {
        "trade_id": f"{side}-{net}",
        "candidate_id_entry": f"candidate-{side}",
        "side": side,
        "strategy": "momentum",
        "entry_timestamp": "2026-01-01T00:00:00",
        "entry_price": 100.0,
        "exit_price": 101.0 if side == "LONG" else 99.0,
        "exit_reason": "take_profit" if net > 0 else "stop_loss",
        "gross_pnl": gross,
        "fees": 1.0,
        "slippage": 2.0,
        "net_pnl": net,
        "duration_hours": 4,
        "setup_quality": "acceptable",
        "setup_quality_score": 0.6,
        "confidence": 0.6,
        "risk_fraction": 0.003,
        "risk_reward_initial": 2.0,
        "entry_decision": {"reasoning_summary": "mock", "take_profit": 102.0},
        "candidate_setup": {"baseline_policy": "state_aware_momentum"},
        "market_regime_entry": {"trend": "uptrend" if side == "LONG" else "downtrend"},
        "trend_short_entry": "up" if side == "LONG" else "down",
        "trend_long_entry": "up" if side == "LONG" else "down",
        "volatility_entry": 0.01,
        "derivatives_availability_entry": {"funding": "unavailable"},
    }


def _write_report(path: Path, label: str, ledger: list[dict]) -> None:
    path.write_text(
        json.dumps(
            {
                "version": "test",
                "window_label": label,
                "candidates_submitted": 1,
                "decision_distribution": {"LONG": 1},
                "setup_quality_distribution": {"acceptable": 1},
                "final_parse_success_rate": 1.0,
                "risk_rejects": 0,
                "ledger_pnl_matches_official": True,
                "realized_pnl": sum(item["net_pnl"] for item in ledger),
                "fees": sum(item["fees"] for item in ledger),
                "slippage": sum(item["slippage"] for item in ledger),
                "closed_trades_ledger": ledger,
                "reviews": [{"candidate": {"candidate_id": "mock"}}],
            }
        ),
        encoding="utf-8",
    )
