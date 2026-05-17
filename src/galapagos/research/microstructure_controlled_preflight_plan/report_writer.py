import json
from pathlib import Path
from typing import Any

class PreflightPlanReportWriter:
    def __init__(self, version: str):
        self.version = version
        self.v_norm = version.lower().replace(".", "_")
        self.reports_dir = Path("reports/research")
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def write_report(self, name: str, payload: Any, title: str, lines: list[str]):
        # JSON
        filename = name
        if self.v_norm not in name:
            filename = f"{name}_{self.v_norm}"
            
        json_path = self.reports_dir / f"{filename}.json"
        with open(json_path, "w") as f:
            json.dump(payload, f, indent=2)
            
        # Markdown
        md_path = self.reports_dir / f"{filename}.md"
        with open(md_path, "w") as f:
            f.write(f"# {title} ({self.version})\n\n")
            for line in lines:
                f.write(f"- {line}\n")
            f.write(f"\n```json\n{json.dumps(payload, indent=2)}\n```\n")

