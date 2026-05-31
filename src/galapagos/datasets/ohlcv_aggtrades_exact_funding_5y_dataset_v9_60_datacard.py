from __future__ import annotations

from typing import Any


def build_dataset_datacard_v9_60(report: dict[str, Any]) -> str:
    window = report.get("target_window", {})
    return (
        "# Datacard V9.60 - Dataset funding common window\n\n"
        f"- Fenetre : `{window.get('start')}` -> `{window.get('end')}`.\n"
        f"- Target : `{report.get('target_name')}`.\n"
        f"- Dataset cree : `{report.get('dataset_created')}`.\n"
        f"- Decision : `{report.get('decision')}`.\n"
        f"- Splits : `{report.get('dataset_design', {}).get('split_policy')}`.\n\n"
        "Dataset supervise offline research-only. Aucun ML, backtest, walk-forward, strategie ou signal n'est execute par V9.60.\n"
    )
