from __future__ import annotations
import json
from pathlib import Path

from galapagos.utils.version import normalize_version

def write_report(data: dict, name: str, version: str) -> None:
    report_dir = Path("reports/research")
    report_dir.mkdir(parents=True, exist_ok=True)

    suffix = normalize_version(version)
    json_path = report_dir / f"{name}_{suffix}.json"
    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)

    md_path = report_dir / f"{name}_{suffix}.md"
    with open(md_path, "w") as f:
        f.write(f"# {name.replace('_', ' ').title()}\n\n")
        f.write("```json\n")
        f.write(json.dumps(data, indent=2))
        f.write("\n```\n")
