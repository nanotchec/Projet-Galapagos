from __future__ import annotations


def count_no_trade(decisions: list[dict]) -> int:
    return sum(1 for decision in decisions if decision.get("decision") == "NO_TRADE")

