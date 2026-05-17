from __future__ import annotations

from typing import Any

from galapagos.research.report_models import write_research_report


def write_extension_gate_report(*, name: str, payload: dict[str, Any], output_dir: str = "reports/research") -> dict[str, str]:
    return write_research_report(
        name=name,
        payload=payload,
        title=name.replace("_", " ").title(),
        lines=[
            "Rapport V1.86 de gate d'approbation humaine.",
            "La version autorise uniquement une future V1.87 si la phrase exacte est fournie.",
            "Aucune matérialisation, aucune écriture data, aucun réseau, aucun ML, aucun trading.",
        ],
        output_dir=output_dir,
    )
