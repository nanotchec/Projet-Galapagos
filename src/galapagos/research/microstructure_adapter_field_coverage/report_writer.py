from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any

class ReportWriter:
    def __init__(self, output_dir: str = "reports/research"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_json(self, name: str, data: Dict[str, Any]):
        path = self.output_dir / f"{name}.json"
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def write_md(self, name: str, title: str, content: Dict[str, Any]):
        path = self.output_dir / f"{name}.md"
        with open(path, "w") as f:
            f.write(f"# {title}\n\n")
            for k, v in content.items():
                f.write(f"## {k}\n")
                f.write(f"```json\n{json.dumps(v, indent=2)}\n```\n\n")
