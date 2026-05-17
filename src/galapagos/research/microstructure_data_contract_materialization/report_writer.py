from __future__ import annotations

from typing import Any

from galapagos.research.report_models import write_research_report


def write_materialization_report(
    *, name: str, payload: dict[str, Any], output_dir: str = "reports/research"
) -> dict[str, str]:
    title = name.replace("_", " ").title()
    lines = [
        "Rapport V1.84 de micro-matérialisation ultra-bornée.",
        "Aucun réseau, aucun ML, aucun paper live, aucun trading réel.",
        "Les seules écritures data autorisées sont les trois JSON V1.84 explicitement listés.",
    ]
    return write_research_report(name=name, payload=payload, title=title, lines=lines, output_dir=output_dir)
