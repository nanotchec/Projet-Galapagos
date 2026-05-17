from __future__ import annotations

from typing import Any

from galapagos.research.report_models import write_research_report


def write_ensemble_lab_report(
    version: str,
    payload: dict[str, Any],
    output_dir: str = "reports/research",
) -> None:
    """Generate the main ensemble signal lab report."""
    name = f"ensemble_signal_lab_{version}"
    title = f"Ensemble Signal Lab {version.upper()}"
    
    # Extract some summary lines
    methods = payload.get("methods_evaluated", [])
    best_method = payload.get("best_method", "N/A")
    
    lines = [
        f"Ensemble methods evaluated: {', '.join(methods)}.",
        f"Best performing method: {best_method}.",
        f"Reviewer candidates generated: {payload.get('candidates_count', 0)}.",
        f"Final Verdict: {payload.get('verdict', 'UNKNOWN')}.",
    ]
    
    write_research_report(
        name=name,
        payload=payload,
        title=title,
        lines=lines,
        output_dir=output_dir,
    )
