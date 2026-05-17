"""Report writer for Microstructure Data Enrichment Spec (V1.52)."""
import json
from pathlib import Path

class EnrichmentReportWriter:
    def __init__(self, version, report_dir="reports/research"):
        self.version = version
        self.v_norm = version.lower().replace(".", "_")
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def write_report(self, name, data):
        json_path = self.report_dir / f"{name}_{self.v_norm}.json"
        if name == f"{self.v_norm}_recommendation":
             json_path = self.report_dir / f"{name}.json"
             
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)
        
        md_path = json_path.with_suffix(".md")
        md_content = f"# {name.replace('_', ' ').title()} ({self.version})\n\n"
        md_content += "```json\n" + json.dumps(data, indent=2) + "\n```\n"
        md_path.write_text(md_content)
        return json_path
