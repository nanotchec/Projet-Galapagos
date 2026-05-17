from __future__ import annotations
import json
from pathlib import Path


class CollectorReportWriter:
    """Writes V1.54 collector reports to JSON and MD formats."""

    def __init__(self, version: str):
        self.version = version
        self.v_norm = version.lower().replace(".", "_")
        self.out_dir = Path("reports/research")
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def write_report(self, base_name: str, payload: dict) -> None:
        """Writes both JSON and MD."""
        # Fix the base_name if it doesn't already have the version suffix
        if self.v_norm not in base_name:
            base_name = f"{base_name}_{self.v_norm}"
            
        json_path = self.out_dir / f"{base_name}.json"
        md_path = self.out_dir / f"{base_name}.md"

        # Ensure no NaN or Infinity
        dumped = json.dumps(payload, indent=2)
        if "NaN" in dumped or "Infinity" in dumped:
            raise ValueError(f"Finiteness issue detected in {base_name}")

        with open(json_path, "w") as f:
            f.write(dumped)

        with open(md_path, "w") as f:
            f.write(f"# {base_name.replace('_', ' ').title()}\n\n")
            f.write("```json\n")
            f.write(dumped)
            f.write("\n```\n")
