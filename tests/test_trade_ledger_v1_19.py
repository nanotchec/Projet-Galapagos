"""Tests for Trade Ledger and V1.19 evaluation logic."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from galapagos.research.trade_ledger.policy import atr_proxy_policy, fixed_percent_policy
from galapagos.research.trade_ledger.schema import TradeCandidate, TradeSide


def test_trade_candidate_validation():
    """Verify TradeCandidate schema and validation rules."""
    ts = datetime.now(UTC)
    
    # Valid LONG
    cand = TradeCandidate(
        candidate_id="test_1",
        timestamp=ts,
        side=TradeSide.LONG,
        entry_price=100.0,
        stop_loss=95.0,
        take_profit=110.0,
        max_holding_bars=6,
        max_holding_time=ts,
        source="test",
        source_version="v1",
        policy_name="fixed",
        policy_version="v1",
    )
    assert cand.side == TradeSide.LONG
    
    # Invalid LONG (SL above entry)
    with pytest.raises(ValidationError):
        TradeCandidate(
            candidate_id="test_2",
            timestamp=ts,
            side=TradeSide.LONG,
            entry_price=100.0,
            stop_loss=105.0,
            max_holding_bars=6,
            max_holding_time=ts,
            source="test",
            source_version="v1",
            policy_name="fixed",
            policy_version="v1",
        )

    # Valid SHORT
    cand_short = TradeCandidate(
        candidate_id="test_3",
        timestamp=ts,
        side=TradeSide.SHORT,
        entry_price=100.0,
        stop_loss=105.0,
        take_profit=90.0,
        max_holding_bars=6,
        max_holding_time=ts,
        source="test",
        source_version="v1",
        policy_name="fixed",
        policy_version="v1",
    )
    assert cand_short.side == TradeSide.SHORT


def test_fixed_policy():
    """Verify fixed percent policy values."""
    res = fixed_percent_policy(100.0, "LONG")
    assert res["stop_loss"] == 98.5
    assert res["take_profit"] == 103.0


def test_atr_policy():
    """Verify ATR proxy policy with caps."""
    # 2% ATR
    res = atr_proxy_policy(100.0, "LONG", 0.02)
    # SL = 1.5 * 2% = 3%
    assert res["stop_loss"] == 97.0
    # TP = 2.0 * 3% = 6%
    assert res["take_profit"] == 106.0
    
    # Very high ATR (10%) -> should cap SL at 5%
    res_high = atr_proxy_policy(100.0, "LONG", 0.10)
    assert res_high["stop_loss"] == 95.0 # capped at 5%
