from __future__ import annotations

from typing import Any

from galapagos.research.report_models import write_research_report


def write_training_dataset_readiness_report(name: str, payload: dict[str, Any], *, output_dir: str = "reports/research") -> dict[str, str]:
    title = name.replace("_", " ").title()
    lines = [
        f"Version : {payload.get('version', 'V1.98')}.",
        "Phase reports-only : aucun data write, aucun dataset d'entrainement, aucun ML, aucun backtest.",
        f"Verdict : {payload.get('final_verdict', payload.get('consistency_check_status', 'n/a'))}.",
    ]
    return write_research_report(name=name, payload=payload, title=title, lines=lines, output_dir=output_dir)
