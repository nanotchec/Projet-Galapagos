"""Helpers for writing failure analysis reports."""
from __future__ import annotations

import json
from pathlib import Path


def write_failure_report(
    name: str, payload: dict, title: str, lines: list[str], output_dir: str | Path
) -> None:
    """Write both .json and .md files for a failure analysis report."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / f"{name}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    md_path = out_dir / f"{name}.md"
    md_content = [f"# {title}", ""]
    for line in lines:
        md_content.append(line)
    md_content.append("")
    md_content.append("## Raw Payload")
    md_content.append("```json")
    md_content.append(json.dumps(payload, indent=2, ensure_ascii=False))
    md_content.append("```")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_content))
