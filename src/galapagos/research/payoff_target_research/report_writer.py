"""Write research reports for V1.42."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

def write_json_report(data: dict[str, Any], path: str | Path) -> None:
    """Write data to a JSON file."""
    Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")

def write_md_report(title: str, data: dict[str, Any], path: str | Path) -> None:
    """Write a simple MD summary of the data."""
    lines = [f"# {title}", ""]
    for key, value in data.items():
        if isinstance(value, list):
            lines.append(f"- **{key}**:")
            for item in value:
                lines.append(f"  - {item}")
        elif isinstance(value, dict):
            lines.append(f"- **{key}**: (dictionary)")
        else:
            lines.append(f"- **{key}**: {value}")
    
    Path(path).write_text("\n".join(lines), encoding="utf-8")
