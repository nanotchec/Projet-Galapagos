"""Report writing helpers for payoff-aware objective research."""
from __future__ import annotations

from typing import Any

from galapagos.research.report_models import write_research_report


def write_payoff_objective_report(
    name: str,
    payload: dict[str, Any],
    *,
    title: str,
    lines: list[str],
    output_dir: str = "reports/research",
) -> dict[str, str]:
    return write_research_report(name=name, payload=payload, title=title, lines=lines, output_dir=output_dir)

