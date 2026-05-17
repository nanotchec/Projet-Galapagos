"""Report writer for V1.51 research."""
import json
from pathlib import Path
from typing import Dict, Any

class QualityMaskReportWriter:
    def __init__(self, version: str, output_dir: str = "reports/research"):
        self.version = version
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_report(self, name: str, data: Dict[str, Any], title: str):
        json_path = self.output_dir / f"{name}_{self.version.lower().replace('.', '_')}.json"
        if name == "v1_51_recommendation":
             json_path = self.output_dir / f"{name}.json"
             
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)
            
        md_path = json_path.with_suffix(".md")
        with open(md_path, "w") as f:
            f.write(f"# {title}\n\n")
            f.write("```json\n")
            f.write(json.dumps(data, indent=2))
            f.write("\n```\n")
