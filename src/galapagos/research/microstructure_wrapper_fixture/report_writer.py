import json
import os
from pathlib import Path
from typing import Any, Dict

class ReportWriter:
    """Writes the final reports in JSON and MD format."""
    def __init__(self, version: str):
        self.version = version
        self.output_dir = Path("reports/research")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_json(self, name: str, data: Dict[str, Any]) -> str:
        filename = f"{name}_{self.version.replace('.', '_').lower()}.json"
        if name == "v1_64_recommendation":
             filename = "v1_64_recommendation.json"
             
        path = self.output_dir / filename
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return str(path)

    def write_md(self, name: str, data: Dict[str, Any]) -> str:
        filename = f"{name}_{self.version.replace('.', '_').lower()}.md"
        if name == "v1_64_recommendation":
             filename = "v1_64_recommendation.md"

        path = self.output_dir / filename
        
        lines = [f"# {name.replace('_', ' ').title()} - {self.version}", ""]
        for k, v in data.items():
            lines.append(f"- **{k}**: {v}")
            
        with open(path, "w") as f:
            f.write("\n".join(lines))
        return str(path)
