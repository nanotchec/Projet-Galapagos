from __future__ import annotations
import json
from pathlib import Path

class ReportWriter:
    def __init__(self, output_dir: str = "reports/research"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_json(self, name: str, data: dict[str, Any]):
        path = self.output_dir / f"{name}.json"
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def write_md(self, name: str, title: str, sections: dict[str, Any]):
        path = self.output_dir / f"{name}.md"
        with open(path, "w") as f:
            f.write(f"# {title}\n\n")
            for section_title, content in sections.items():
                f.write(f"## {section_title}\n")
                if isinstance(content, dict):
                    f.write("```json\n")
                    f.write(json.dumps(content, indent=2))
                    f.write("\n```\n\n")
                else:
                    f.write(f"{content}\n\n")
