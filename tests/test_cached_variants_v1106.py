from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from galapagos.agent.decision_schema import AgentDecision
from galapagos.analysis.variant_comparison import summarize_variant_windows


def test_cost_filter_blocks_low_expected_move() -> None:
    module = _load_script("run_codex_setup_review")
    decision = _long_decision()
    result = module._apply_variant_filters(
        decision,
        decision_context_payload={
            "costs": {
                "candidate_expected_move": 0.002,
                "estimated_round_trip_cost": 0.003,
            },
            "market": {"market_regime": {"trend": "uptrend"}},
        },
        filter_config={
            "cost_filter": {
                "enabled": True,
                "min_expected_move_to_cost_ratio": 2.0,
            }
        },
    )
    assert result["blocked_by_cost_filter"] is True
    assert result["decision"].decision.value == "NO_TRADE"


def test_regime_filter_blocks_downtrend_long() -> None:
    module = _load_script("run_codex_setup_review")
    result = module._apply_variant_filters(
        _long_decision(),
        decision_context_payload={
            "costs": {},
            "market": {"market_regime": {"trend": "downtrend"}},
        },
        filter_config={
            "regime_filter": {
                "enabled": True,
                "block_long_trends": ["downtrend"],
            }
        },
    )
    assert result["blocked_by_regime_filter"] is True
    assert result["decision"].decision.value == "NO_TRADE"


def test_variant_comparison_aggregates() -> None:
    comparison = summarize_variant_windows(
        {
            "a": [
                {"window": "calibration", "final_equity_pnl": 1, "ledger_trade_count": 1},
                {"window": "validation_1", "final_equity_pnl": -2, "ledger_trade_count": 1},
            ],
            "b": [
                {"window": "calibration", "final_equity_pnl": 0, "ledger_trade_count": 0},
                {"window": "validation_1", "final_equity_pnl": 0, "ledger_trade_count": 0},
            ],
        }
    )
    assert comparison["best_total_pnl"]["variant"] == "b"
    assert comparison["most_stable"]["variant"] == "b"


def test_variant_runner_blocks_holdout_config(tmp_path: Path) -> None:
    module = _load_script("replay_cached_variants")
    config = tmp_path / "variants.yaml"
    config.write_text(
        """
version: V1.10.6
profile: galapagos_4h
asset: BTC/USD
timeframe: 4h
holdout_enabled: false
windows:
  holdout:
    max_candidates: 20
variants: {}
""",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="Holdout is blocked"):
        module.replay_cached_variants(config_path=config, cache_readonly=True)


def _long_decision() -> AgentDecision:
    return AgentDecision(
        decision="LONG",
        profile="galapagos_4h",
        asset="BTC/USD",
        strategy="momentum",
        confidence=0.7,
        reasoning_summary="Mock long.",
        horizon="4h",
        reference_entry_price=100.0,
        stop_loss=98.0,
        take_profit=104.0,
        risk_fraction=0.01,
        max_duration_minutes=240,
        invalidation_conditions=[],
        critical_data_used=["price", "volatility"],
        setup_quality="acceptable",
        setup_quality_score=0.5,
    )


def _load_script(name: str):
    sys.path.insert(0, str(Path("scripts").resolve()))
    path = Path("scripts") / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module
