"""Report writer for microstructure coverage quality diagnostic."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

class CoverageReportWriter:
    """Writes JSON and MD reports for V1.50."""
    
    def __init__(self, output_dir: str | Path, version: str):
        self.output_dir = Path(output_dir)
        self.version = version
        self.version_norm = version.lower().replace(".", "_")
        
    def write_report(self, name: str, data: dict[str, Any], title: str):
        """Writes a single report (JSON + MD) with version suffix."""
        filename = f"{name}_{self.version_norm}"
        self._write(filename, data, title)
        
    def write_raw_report(self, filename: str, data: dict[str, Any], title: str):
        """Writes a single report (JSON + MD) without version suffix."""
        self._write(filename, data, title)
        
    def _write(self, filename: str, data: dict[str, Any], title: str):
        # JSON
        json_path = self.output_dir / f"{filename}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        # MD
        md_path = self.output_dir / f"{filename}.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# {title} - {self.version}\n\n")
            f.write("```json\n")
            f.write(json.dumps(data, indent=2, ensure_ascii=False))
            f.write("\n```\n")
            
    def write_doc(self, content: str):
        """Writes the final documentation file."""
        doc_dir = self.output_dir.parent.parent / "docs"
        doc_dir.mkdir(parents=True, exist_ok=True)
        doc_path = doc_dir / f"microstructure_coverage_quality_{self.version_norm}.md"
        with open(doc_path, "w", encoding="utf-8") as f:
            f.write(content)
