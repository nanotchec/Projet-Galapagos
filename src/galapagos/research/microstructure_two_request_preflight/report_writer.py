import json
from pathlib import Path
from typing import Any, Dict

class ReportWriter:
    def __init__(self, root: Path, version: str):
        self.root = root
        self.version = version
        self.v_norm = version.replace(".", "_").lower()

    def write_report(self, stem: str, data: Dict[str, Any], exact_name: bool = False):
        reports_dir = self.root / "reports/research"
        reports_dir.mkdir(parents=True, exist_ok=True)

        # JSON
        if exact_name:
            json_p = reports_dir / f"{stem}.json"
        else:
            json_p = reports_dir / f"{stem}_{self.v_norm}.json"
        
        with open(json_p, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # MD (simplified)
        if exact_name:
            md_p = reports_dir / f"{stem}.md"
        else:
            md_p = reports_dir / f"{stem}_{self.v_norm}.md"
        
        with open(md_p, "w") as f:
            f.write(f"# {stem.replace('_', ' ').title()}\n\n")
            f.write(f"Version: {self.version}\n\n")
            f.write("```json\n")
            f.write(json.dumps(data, indent=2, ensure_ascii=False))
            f.write("\n```\n")
