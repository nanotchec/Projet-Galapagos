"""Report helpers for signal selection research."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.research.report_models import write_research_report
from galapagos.utils.version import display_version, normalize_version


def report_name(stem: str, version: str) -> str:
    return f"{stem}_{normalize_version(version)}"


def write_selection_report(
    *,
    stem: str,
    version: str,
    payload: dict[str, Any],
    title: str,
    lines: list[str],
    output_dir: str | Path = "reports/research",
) -> dict[str, str]:
    return write_research_report(
        name=report_name(stem, version),
        payload=payload,
        title=f"{title} {display_version(version)}",
        lines=lines,
        output_dir=output_dir,
    )

def save_signal_report(name: str, payload: dict[str, Any], output_dir: str = "reports/research"):
    """Simplified helper for saving signal reports."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    # Save JSON
    json_path = out_path / f"{name}.json"
    with open(json_path, "w") as f:
        json.dump(payload, f, indent=2)
        
    # Save MD (minimalist)
    md_path = out_path / f"{name}.md"
    md_lines = [
        f"# {name.replace('_', ' ').title()}", 
        "", 
        "```json", 
        json.dumps(payload, indent=2), 
        "```"
    ]
    md_path.write_text("\n".join(md_lines))
    return json_path
