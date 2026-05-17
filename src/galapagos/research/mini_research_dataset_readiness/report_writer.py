from __future__ import annotations

from typing import Any

from galapagos.research.report_models import write_research_report


def write_readiness_report(name: str, payload: dict[str, Any]) -> dict[str, str]:
    return write_research_report(
        name=name,
        payload=payload,
        title=name.replace("_", " ").title(),
        lines=["Rapport V1.91 reports-only."],
        output_dir="reports/research",
    )
