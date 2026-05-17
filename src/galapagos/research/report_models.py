from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_research_report(
    *,
    name: str,
    payload: dict[str, Any],
    title: str,
    lines: list[str],
    output_dir: str | Path = "reports/research",
) -> dict[str, str]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / f"{name}.json"
    md_path = output / f"{name}.md"
    json_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    md_path.write_text("\n".join([f"# {title}", "", *lines]), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}
