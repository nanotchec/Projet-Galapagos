from __future__ import annotations

from typing import Any


def build_dataset_datacard_v9_65(report: dict[str, Any]) -> str:
    return (
        "# Datacard V9.65 - Dataset label redesign 5Y\n\n"
        f"- Decision : `{report['decision']}`.\n"
        f"- Target : `{report['target_name']}`.\n"
        f"- Fenetre : `{report['target_window']['label']}`.\n"
        "- Features : OHLCV + aggTrades exact V9.47, sans funding.\n"
        "- Labels : V9.64, selection methodologique V9.63.\n"
        "- Splits : temporels 60/20/20, sans shuffle.\n"
        "- Aucun ML, walk-forward, backtest, strategie, signal ou ordre dans V9.65.\n"
    )
