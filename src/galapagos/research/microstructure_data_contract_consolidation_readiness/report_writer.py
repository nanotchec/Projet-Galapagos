from __future__ import annotations

from typing import Any

from galapagos.research.report_models import write_research_report


def write_consolidation_readiness_report(
    *, name: str, payload: dict[str, Any], output_dir: str = "reports/research"
) -> dict[str, str]:
    return write_research_report(
        name=name,
        payload=payload,
        title=name.replace("_", " ").title(),
        lines=[
            "Rapport V1.89 de readiness consolidation et gate d'approbation.",
            "La version audite les artefacts V1.84/V1.87, conçoit V2 en dry-plan et ne modifie pas data/.",
            "Aucun réseau, aucun ML, aucun paper live, aucun trading réel.",
        ],
        output_dir=output_dir,
    )
