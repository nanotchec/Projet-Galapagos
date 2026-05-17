from __future__ import annotations

from typing import Any

from galapagos.research.report_models import write_research_report


def write_feature_preview_report(name: str, payload: dict[str, Any], *, output_dir: str = "reports/research") -> dict[str, str]:
    return write_research_report(
        name=name,
        payload=payload,
        title=name.replace("_", " ").title(),
        lines=[
            f"Version : {payload.get('version', 'V1.95')}.",
            "Preview de features ultra-bornee, JSON uniquement.",
            "Aucun label, target, prediction, ML, trading ou ordre reel.",
        ],
        output_dir=output_dir,
    )
