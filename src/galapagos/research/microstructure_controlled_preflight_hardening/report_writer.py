import json
from pathlib import Path

class ReportWriter:
    def __init__(self, version: str):
        self.version = version
        self.reports_dir = Path("reports/research")
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def write_report(self, stem: str, data: dict, title: str, description: list):
        v_suffix = self.version.lower().replace(".", "_")
        filename_json = f"{stem}_{v_suffix}.json"
        if stem == "v1_61_recommendation":
             filename_json = "v1_61_recommendation.json"
             
        with open(self.reports_dir / filename_json, "w") as f:
            json.dump(data, f, indent=2)

        filename_md = f"{stem}_{v_suffix}.md"
        if stem == "v1_61_recommendation":
             filename_md = "v1_61_recommendation.md"
             
        with open(self.reports_dir / filename_md, "w") as f:
            f.write(f"# {title}\n\n")
            for line in description:
                f.write(f"{line}\n")
            f.write("\n```json\n")
            f.write(json.dumps(data, indent=2))
            f.write("\n```\n")
