from __future__ import annotations

import json
from pathlib import Path
from typing import Any

def save_research_report(name: str, data: dict[str, Any]):
    """Save report in JSON and MD."""
    base = Path("reports/research")
    base.mkdir(parents=True, exist_ok=True)
    
    json_path = base / f"{name}.json"
    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)
        
    md_path = base / f"{name}.md"
    with open(md_path, "w") as f:
        f.write(f"# {name.replace('_', ' ').title()}\n\n")
        f.write("```json\n")
        f.write(json.dumps(data, indent=2))
        f.write("\n```\n")
