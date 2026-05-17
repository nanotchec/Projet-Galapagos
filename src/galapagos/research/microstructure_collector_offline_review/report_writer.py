import json
from pathlib import Path
from typing import Dict, Any

class OfflineReviewReportWriter:
    """Writes JSON and MD reports for V1.58."""
    
    def __init__(self, version: str = "v1.58", reports_dir: str = "reports/research"):
        self.version = version
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def _get_filename(self, name: str, ext: str) -> str:
        # Standardize suffix for filenames to lowercase with underscores
        v_suffix = self.version.lower().replace(".", "_")
        if v_suffix in name.lower().replace(".", "_"):
            return f"{name}.{ext}"
        return f"{name}_{v_suffix}.{ext}"

    def write_json(self, name: str, data: Dict[str, Any]):
        filename = self._get_filename(name, "json")
        path = self.reports_dir / filename
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def write_md(self, name: str, title: str, content: str):
        filename = self._get_filename(name, "md")
        path = self.reports_dir / filename
        with open(path, "w") as f:
            f.write(f"# {title} ({self.version})\n\n")
            f.write(content)

    def write_pair(self, name: str, title: str, payload: Dict[str, Any]):
        self.write_json(name, payload)
        
        md_lines = []
        for k, v in payload.items():
            md_lines.append(f"- **{k}**: {v}")
        self.write_md(name, title, "\n".join(md_lines))
