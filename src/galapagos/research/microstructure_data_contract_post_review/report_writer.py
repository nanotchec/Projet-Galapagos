from __future__ import annotations

from typing import Any

from galapagos.research.report_models import write_research_report


def write_post_review_report(*, name: str, payload: dict[str, Any], output_dir: str = "reports/research") -> dict[str, str]:
    return write_research_report(
        name=name,
        payload=payload,
        title=name.replace("_", " ").title(),
        lines=[
            "Rapport V1.85 de review post-matérialisation.",
            "La version lit les artefacts data V1.84 sans les modifier.",
            "Aucun réseau, aucun ML, aucun paper live, aucun trading réel.",
        ],
        output_dir=output_dir,
    )
