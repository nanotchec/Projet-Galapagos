import json
from pathlib import Path

class DryRunReportWriter:
    def __init__(self, version: str):
        self.version = version
        self.reports_dir = Path("reports/research")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.v_norm = version.lower().replace(".", "_")

    def write_report(self, stem: str, data: dict, title: str, description: list):
        # Handle cases where stem already includes version or not
        if self.v_norm in stem:
            filename_json = f"{stem}.json"
            filename_md = f"{stem}.md"
        else:
            filename_json = f"{stem}_{self.v_norm}.json"
            filename_md = f"{stem}_{self.v_norm}.md"

        # JSON
        with open(self.reports_dir / filename_json, "w") as f:
            json.dump(data, f, indent=2)

        # MD
        md_content = f"# {title}\n\n"
        for line in description:
            md_content += f"{line}\n"
        md_content += f"\n- **Version**: {self.version}\n"
        md_content += f"- **Status**: {data.get('status', 'COMPLETED')}\n\n"
        md_content += "```json\n"
        md_content += json.dumps(data, indent=2)
        md_content += "\n```\n"

        with open(self.reports_dir / filename_md, "w") as f:
            f.write(md_content)
