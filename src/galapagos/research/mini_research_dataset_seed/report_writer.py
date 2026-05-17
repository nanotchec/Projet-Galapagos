from __future__ import annotations

from typing import Any

from galapagos.research.report_models import write_research_report


def write_seed_report(name: str, payload: dict[str, Any]) -> dict[str, str]:
    return write_research_report(
        name=name,
        payload=payload,
        title=name.replace("_", " ").title(),
        lines=[
            "Rapport V1.92 : mini research dataset seed ultra-borne.",
            "Aucun reseau, aucun ML, aucun paper live, aucun trading reel.",
        ],
        output_dir="reports/research",
    )
