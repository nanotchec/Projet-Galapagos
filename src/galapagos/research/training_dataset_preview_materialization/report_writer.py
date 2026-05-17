from __future__ import annotations

from typing import Any

from galapagos.research.report_models import write_research_report


def write_training_dataset_preview_report(name: str, payload: dict[str, Any]) -> dict[str, str]:
    return write_research_report(
        name=name,
        payload=payload,
        title=name.replace("_", " ").title(),
        lines=[
            f"Rapport {payload.get('version', 'V1.99')}.",
            "Preview physique ultra-bornee features+labels, sans ML, sans backtest, sans trading.",
        ],
        output_dir="reports/research",
    )
