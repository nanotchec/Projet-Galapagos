from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pandas as pd
import pytest

from galapagos.research.trade_ledger.intrabar_evaluator import evaluate_trade_candidates_intrabar
from galapagos.research.trade_ledger.schema import TradeCandidate, TradeSide


def test_trade_candidate_temporal_consistency():
    """Test that entry_time >= signal_time and max_holding_time > entry_time."""
    signal_time = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    
    # Valid
    cand = TradeCandidate(
        candidate_id="test",
        signal_time=signal_time,
        entry_time=signal_time + timedelta(hours=4),
        side=TradeSide.LONG,
        entry_price=100.0,
        max_holding_bars=6,
        max_holding_time=signal_time + timedelta(hours=28),
        source="test",
        source_version="v1.19.1",
        policy_name="test",
        policy_version="v1.19.1",
    )
    assert cand.entry_time > cand.signal_time
    
    # Invalid: entry before signal
    with pytest.raises(ValueError, match="entry_time .* must be >= signal_time"):
        TradeCandidate(
            candidate_id="test",
            signal_time=signal_time,
            entry_time=signal_time - timedelta(hours=1),
            side=TradeSide.LONG,
            entry_price=100.0,
            max_holding_bars=6,
            max_holding_time=signal_time + timedelta(hours=28),
            source="test",
            source_version="v1.19.1",
            policy_name="test",
            policy_version="v1.19.1",
        )

    # Invalid: max_holding before entry
    with pytest.raises(ValueError, match="max_holding_time .* must be > entry_time"):
        TradeCandidate(
            candidate_id="test",
            signal_time=signal_time,
            entry_time=signal_time + timedelta(hours=4),
            side=TradeSide.LONG,
            entry_price=100.0,
            max_holding_bars=6,
            max_holding_time=signal_time + timedelta(hours=3),
            source="test",
            source_version="v1.19.1",
            policy_name="test",
            policy_version="v1.19.1",
        )

def test_intrabar_evaluator_ignores_before_entry():
    """Test that evaluator only uses intrabar data from entry_time onwards."""
    signal_time = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    entry_time = signal_time + timedelta(hours=4)
    max_holding = entry_time + timedelta(hours=24)
    
    cand = TradeCandidate(
        candidate_id="test",
        signal_time=signal_time,
        entry_time=entry_time,
        side=TradeSide.LONG,
        entry_price=100.0,
        stop_loss=90.0,
        take_profit=120.0,
        max_holding_bars=6,
        max_holding_time=max_holding,
        source="test",
        source_version="v1.19.1",
        policy_name="test",
        policy_version="v1.19.1",
    )
    
    # Intrabar data with a "fake" TP hit before entry_time
    intrabar_data = [
        {
            "timestamp": signal_time + timedelta(minutes=5),
            "open": 100,
            "high": 125,
            "low": 100,
            "close": 125,
        },
        {
            "timestamp": entry_time + timedelta(minutes=5),
            "open": 100,
            "high": 105,
            "low": 100,
            "close": 105,
        },
        {"timestamp": max_holding, "open": 110, "high": 110, "low": 110, "close": 110},
    ]
    intrabar_df = pd.DataFrame(intrabar_data)
    
    results = evaluate_trade_candidates_intrabar([cand], intrabar_df)
    res = results[0]
    
    # Should NOT have exited at 125 because it was before entry_time
    assert res.exit_reason == "timeout"
    assert res.exit_price == 110.0
    assert res.exit_time == max_holding
