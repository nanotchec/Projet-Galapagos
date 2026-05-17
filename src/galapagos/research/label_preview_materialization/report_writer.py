from __future__ import annotations

from typing import Any

from galapagos.research.report_models import write_research_report


def write_label_preview_report(name: str, payload: dict[str, Any], *, output_dir: str = "reports/research") -> dict[str, str]:
    return write_research_report(
        name=name,
        payload=payload,
        title=name.replace("_", " ").title(),
        lines=[
            f"Version : {payload.get('version', 'V1.97')}.",
            "Materialisation label preview ultra-bornee : JSON seulement, labels separes des features.",
            f"Verdict : {payload.get('final_verdict', payload.get('consistency_check_status', 'n/a'))}.",
        ],
        output_dir=output_dir,
    )

