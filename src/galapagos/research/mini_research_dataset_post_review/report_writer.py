from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.research.report_models import write_research_report


def write_post_review_report(name: str, payload: dict[str, Any], output_dir: str = "reports/research") -> None:
    title = name.replace("_", " ").title()
    lines = [f"Rapport de review post-seed Galapagos {payload.get('version', 'V1.93')}."]
    
    if "final_verdict" in payload:
        lines.append(f"- Verdict final: {payload['final_verdict']}")
    
    if "safety_issues" in payload and payload["safety_issues"]:
        lines.append("- Problemes de securite detectes:")
        for issue in payload["safety_issues"]:
            lines.append(f"  - {issue}")
            
    if "forbidden_seed_term_occurrences" in payload and payload["forbidden_seed_term_occurrences"]:
        lines.append("- Termes interdits detectes:")
        for occ in payload["forbidden_seed_term_occurrences"]:
            lines.append(f"  - {occ}")

    write_research_report(
        name=name,
        payload=payload,
        title=title,
        lines=lines,
        output_dir=output_dir,
    )
