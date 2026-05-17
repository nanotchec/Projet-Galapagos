from __future__ import annotations

from typing import Any

from galapagos.research.report_models import write_research_report


def write_consolidation_report(*, name: str, payload: dict[str, Any], output_dir: str = "reports/research") -> dict[str, str]:
    return write_research_report(
        name=name,
        payload=payload,
        title=name.replace("_", " ").title(),
        lines=[
            "Rapport V1.90 de consolidation ultra-bornée.",
            "La version écrit uniquement trois JSON dans le dossier data V1.90 autorisé.",
            "Aucun réseau, aucun ML, aucun paper live, aucun trading réel.",
        ],
        output_dir=output_dir,
    )
