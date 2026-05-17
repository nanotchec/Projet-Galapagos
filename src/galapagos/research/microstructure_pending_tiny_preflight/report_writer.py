import json
from pathlib import Path
from typing import Any, Dict

class ReportWriter:
    """
    Génère les rapports JSON et MD pour la phase V1.69.1.
    """
    def __init__(self, reports_dir: Path, version: str):
        self.reports_dir = reports_dir
        self.version = version
        self.v_norm = version.replace(".", "_").lower()

    def write_report_no_suffix(self, name: str, data: Dict[str, Any]) -> None:
        p = self.reports_dir / f"{name}.json"
        with open(p, "w") as f:
            json.dump(data, f, indent=2)
        md_p = self.reports_dir / f"{name}.md"
        with open(md_p, "w") as f:
            f.write(f"# Report: {name.replace('_', ' ').title()}\n\n")
            f.write(f"```json\n{json.dumps(data, indent=2)}\n```\n")

    def write_report(self, name: str, data: Dict[str, Any]) -> None:
        p = self.reports_dir / f"{name}_{self.v_norm}.json"
        with open(p, "w") as f:
            json.dump(data, f, indent=2)
        md_p = self.reports_dir / f"{name}_{self.v_norm}.md"
        with open(md_p, "w") as f:
            f.write(f"# Report: {name.replace('_', ' ').title()}\n\n")
            f.write(f"```json\n{json.dumps(data, indent=2)}\n```\n")
