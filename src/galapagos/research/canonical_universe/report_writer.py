import json
from pathlib import Path

def write_universe_reports(reports_dir, reports_data, version):
    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    v_suffix = version.replace(".", "_").lower()
    
    for key, data in reports_data.items():
        filename = f"canonical_{key}_{v_suffix}.json"
        
        # Special naming for summary and recommendation
        if key == "summary":
            filename = f"canonical_universe_summary_{v_suffix}.json"
        elif key == "recommendation":
            prefix = "" if v_suffix.startswith("v") else "v"
            filename = f"{prefix}{v_suffix}_recommendation.json"
        elif key == "counts":
            filename = f"canonical_universe_counts_{v_suffix}.json"
        elif key == "definition":
            filename = f"canonical_universe_definition_{v_suffix}.json"
        elif key == "consistency_check":
            filename = f"canonical_universe_consistency_check_{v_suffix}.json"
            
        path = reports_dir / filename
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
            
        # Write MD equivalent
        md_path = path.with_suffix(".md")
        with open(md_path, "w") as f:
            f.write(f"# Canonical Universe {key.replace('_', ' ').title()} - {version.upper()}\n\n")
            f.write("```json\n")
            f.write(json.dumps(data, indent=2))
            f.write("\n```\n")
