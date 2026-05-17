from __future__ import annotations


def post_mortem_markdown(autopsy: dict) -> str:
    questions = "\n".join(f"- {question}" for question in autopsy.get("questions", []))
    return f"""# Diagnostic post-mortem

## Questions suivies
{questions}

## Etat V1
- Trades perdants: {autopsy.get("losing_trade_count")}
- Decisions refusees/no trade: {autopsy.get("rejected_decision_count")}
- Note: {autopsy.get("notes")}
"""

