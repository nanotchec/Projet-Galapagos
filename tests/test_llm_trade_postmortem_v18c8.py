from __future__ import annotations

import json

from galapagos.analysis.llm_trade_postmortem import (
    analyze_llm_trade_postmortem,
    estimate_risk_reward,
    simulate_filters,
)


def test_risk_reward_calculation() -> None:
    assert estimate_risk_reward(100, 95, 110) == 2.0
    assert estimate_risk_reward(100, 100, 110) is None


def test_filter_summaries() -> None:
    trades = [
        {
            "setup_quality": "acceptable",
            "setup_quality_score": 0.62,
            "confidence": 0.58,
            "risk_reward_ratio": 2.0,
            "estimated_cost_impact": 0.1,
            "net_pnl": 10.0,
        },
        {
            "setup_quality": "poor",
            "setup_quality_score": 0.2,
            "confidence": 0.8,
            "risk_reward_ratio": 1.0,
            "estimated_cost_impact": 0.5,
            "net_pnl": -5.0,
        },
    ]
    result = simulate_filters(trades)
    assert result["setup_quality_score_gte_0_6"]["trade_count"] == 1
    assert result["confidence_gte_0_7"]["trade_count"] == 1
    assert result["risk_reward_gte_1_5"]["pnl"] == 10.0


def test_postmortem_report_generated_from_mock_json(tmp_path) -> None:
    report = tmp_path / "setup.json"
    report.write_text(
        json.dumps(
            {
                "version": "test",
                "reviews": [
                    {
                        "candidate": {
                            "candidate_id": "c1",
                            "decision_timestamp": "2026-01-01T00:00:00",
                            "baseline_policy": "state_aware_momentum",
                            "context_index": 0,
                            "asset": "BTC/USD",
                            "timeframe": "4h",
                        },
                        "decision": "LONG",
                        "raw_response": json.dumps(
                            {
                                "decision": "LONG",
                                "profile": "galapagos_4h",
                                "asset": "BTC/USD",
                                "strategy": "momentum",
                                "confidence": 0.6,
                                "setup_quality": "acceptable",
                                "setup_quality_score": 0.6,
                                "why_not_no_trade": "Aligned.",
                                "reasoning_summary": "Baseline technical setup.",
                                "horizon": "4h",
                                "reference_entry_price": 100.0,
                                "stop_loss": 95.0,
                                "take_profit": 110.0,
                                "risk_fraction": 0.003,
                                "max_duration_minutes": 720,
                                "invalidation_conditions": [],
                                "critical_data_used": ["price", "volatility"],
                            }
                        ),
                        "execution_event": {
                            "position": {
                                "entry_price": 100.0,
                                "size": 1.0,
                                "entry_fee": 0.1,
                                "entry_slippage": 0.05,
                            }
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    analysis = analyze_llm_trade_postmortem(report)
    assert analysis["trades_analyzed"] == 1
    assert analysis["source_of_truth"] == "reconstructed_from_reviews"
    assert analysis["filter_results"]["all_gpt_validated"]["trade_count"] == 1
    assert analysis["trades"][0]["risk_reward_ratio"] == 2.0


def test_postmortem_uses_ledger_when_present(tmp_path) -> None:
    report = tmp_path / "setup_with_ledger.json"
    report.write_text(
        json.dumps(
            {
                "version": "test",
                "realized_pnl": 9.0,
                "fees": 1.0,
                "slippage": 0.2,
                "closed_trades_ledger": [
                    {
                        "trade_id": "t1",
                        "candidate_id_entry": "c1",
                        "profile": "galapagos_4h",
                        "asset": "BTC/USD",
                        "side": "LONG",
                        "strategy": "momentum",
                        "entry_timestamp": "2026-01-01T00:00:00",
                        "entry_price": 100.0,
                        "entry_decision": {
                            "confidence": 0.6,
                            "risk_fraction": 0.003,
                            "reasoning_summary": "Ledger trade.",
                            "stop_loss": 95.0,
                            "take_profit": 110.0,
                        },
                        "exit_timestamp": "2026-01-01T04:00:00",
                        "exit_price": 110.0,
                        "exit_reason": "take_profit",
                        "size": 1.0,
                        "gross_pnl": 10.0,
                        "fees": 1.0,
                        "slippage": 0.2,
                        "net_pnl": 9.0,
                        "net_pnl_percent": 0.09,
                        "duration_bars": 1,
                        "duration_hours": 4,
                        "setup_quality": "acceptable",
                        "setup_quality_score": 0.6,
                        "confidence": 0.6,
                        "risk_fraction": 0.003,
                        "risk_reward_initial": 2.0,
                        "critical_data_used": ["price", "volatility"],
                        "candidate_setup": {"baseline_policy": "state_aware_momentum"},
                        "market_regime_entry": {"trend": "uptrend"},
                        "trend_short_entry": "up",
                        "trend_long_entry": "up",
                        "volatility_entry": 0.01,
                        "derivatives_availability_entry": {"funding": "unavailable"},
                    }
                ],
                "position_events": [
                    {"event_type": "open", "position_id": "t1"},
                    {"event_type": "auto_close", "position_id": "t1"},
                ],
            }
        ),
        encoding="utf-8",
    )
    analysis = analyze_llm_trade_postmortem(report)
    assert analysis["source_of_truth"] == "closed_trades_ledger"
    assert analysis["ledger_pnl_matches_official"] is True
    assert analysis["ledger_pnl_delta"] == 0.0
    assert analysis["aggregations"]["pnl_by_side"]["LONG"]["pnl"] == 9.0
