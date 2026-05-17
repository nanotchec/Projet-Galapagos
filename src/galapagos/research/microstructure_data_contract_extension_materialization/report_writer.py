import json
from pathlib import Path
from typing import Dict, Any

class ReportWriter:
    def __init__(self, version: str = "v1_87"):
        self.version = version
        self.reports_root = Path("reports/research")
        self.reports_root.mkdir(parents=True, exist_ok=True)

    def write_report(self, name: str, data: Dict[str, Any]):
        file_path = self.reports_root / f"microstructure_data_contract_extension_materialization_{name}_{self.version}.json"
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        
        md_path = self.reports_root / f"microstructure_data_contract_extension_materialization_{name}_{self.version}.md"
        with open(md_path, "w") as f:
            f.write(f"# {name.replace('_', ' ').capitalize()} Report {self.version}\n\n")
            f.write("```json\n")
            f.write(json.dumps(data, indent=2))
            f.write("\n```\n")
        return str(file_path)

    def write_recommendation(self, data: Dict[str, Any]):
        file_path = self.reports_root / f"{self.version}_recommendation.json"
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        
        md_path = self.reports_root / f"{self.version}_recommendation.md"
        with open(md_path, "w") as f:
            f.write(f"# Recommendation {self.version}\n\n")
            f.write("```json\n")
            f.write(json.dumps(data, indent=2))
            f.write("\n```\n")

    def write_release_zip_report(self, data: Dict[str, Any]):
        file_path = Path(f"reports/release_zip_{self.version}.json")
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        
        md_path = Path(f"reports/release_zip_{self.version}.md")
        with open(md_path, "w") as f:
            f.write(f"# Release ZIP Report {self.version}\n\n")
            f.write("```json\n")
            f.write(json.dumps(data, indent=2))
            f.write("\n```\n")

    def write_zip_audit_report(self, data: Dict[str, Any]):
        file_path = Path(f"reports/zip_audit_{self.version}.json")
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        
        md_path = Path(f"reports/zip_audit_{self.version}.md")
        with open(md_path, "w") as f:
            f.write(f"# ZIP Audit Report {self.version}\n\n")
            f.write("```json\n")
            f.write(json.dumps(data, indent=2))
            f.write("\n```\n")

    def write_zip_smoke_report(self, data: Dict[str, Any]):
        file_path = Path(f"reports/zip_smoke_test_{self.version}.json")
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        
        md_path = Path(f"reports/zip_smoke_test_{self.version}.md")
        with open(md_path, "w") as f:
            f.write(f"# ZIP Smoke Test Report {self.version}\n\n")
            f.write("```json\n")
            f.write(json.dumps(data, indent=2))
            f.write("\n```\n")
