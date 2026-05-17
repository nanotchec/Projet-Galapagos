from __future__ import annotations


def trade_report_markdown(trade: dict) -> str:
    return f"""# Rapport de trade

- Profil: {trade.get("profile")}
- Strategie: {trade.get("strategy")}
- Side: {trade.get("side")}
- Statut: {trade.get("status")}
- PnL: {trade.get("pnl")}
- Frais: {trade.get("fees")}
- Slippage: {trade.get("slippage")}
"""

