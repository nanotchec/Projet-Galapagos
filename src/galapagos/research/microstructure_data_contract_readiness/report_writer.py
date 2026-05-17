import json
from pathlib import Path
from typing import Any, Dict

class ReportWriter:
    def __init__(self, root: Path, version: str):
        self.root = root
        self.version = version.replace(".", "_").lower()

    def write_report(self, name: str, data: Dict[str, Any], exact_name: bool = False):
        if exact_name:
            base_name = name
        else:
            base_name = f"{name}_{self.version}"
            
        json_p = self.root / f"reports/research/{base_name}.json"
        md_p = self.root / f"reports/research/{base_name}.md"
        
        with open(json_p, "w") as f:
            json.dump(data, f, indent=2)
            
        with open(md_p, "w") as f:
            f.write(f"# {name.replace('_', ' ').title()}\n\n")
            f.write("```json\n")
            f.write(json.dumps(data, indent=2))
            f.write("\n```\n")
