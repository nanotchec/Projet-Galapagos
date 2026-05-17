from pathlib import Path

import pytest

from galapagos.execution.paper_broker import PaperBroker, RealTradingDisabledError


def test_no_real_order_creation_possible() -> None:
    broker = PaperBroker(initial_capital=10_000)
    with pytest.raises(RealTradingDisabledError):
        broker.create_order("BTC/USD", "market", "buy", 1)


def test_no_real_trading_static_scan() -> None:
    root = Path(__file__).resolve().parents[1] / "src"
    dangerous_patterns = [
        ".create_order(",
        "create_market_order",
        "create_limit_order",
        ".withdraw(",
        "privatePost",
    ]
    violations = []
    for path in root.rglob("*.py"):
        if path.name == "future_live_execution.py":
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in dangerous_patterns:
            if pattern in text:
                violations.append(f"{path}: {pattern}")
    assert violations == []
