"""Reporting utilities for intrabar module."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_intrabar_report(
    name: str,
    payload: dict[str, Any],
    title: str,
    lines: list[str],
    output_dir: str = "reports/research",
) -> None:
    """Write an intrabar report in JSON and MD formats."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Write JSON
    json_path = out_dir / f"{name}.json"
    json_path.write_text(json.dumps(payload, indent=2))

    # Write MD
    md_path = out_dir / f"{name}.md"
    md_content = [
        f"# {title}",
        "",
        *lines,
        "",
        "## JSON Payload",
        "```json",
        json.dumps(payload, indent=2),
        "```",
        "",
    ]
    md_path.write_text("\n".join(md_content))
