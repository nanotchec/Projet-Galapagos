import numpy as np
import json
from pathlib import Path

def serialize(obj):
    if isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize(i) for i in obj]
    elif isinstance(obj, (np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, (np.bool_)):
        return bool(obj)
    return obj

def write_v1_35_reports(version, reports_data):
    v_suffix = version.replace(".", "_").lower()
    reports_dir = Path("reports/research")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    serialized_data = serialize(reports_data)
    
    for key, data in serialized_data.items():
        filename = f"source_path_{key}_{v_suffix}.json"
        if key == "summary":
            filename = f"source_path_reconstruction_summary_{v_suffix}.json"
        elif key == "recommendation":
            filename = f"{v_suffix}_recommendation.json"
        elif key == "canonical_path":
            filename = f"canonical_v1_32_4_selection_path_{v_suffix}.json"
        elif key == "ev_proxy_rebuild":
            filename = f"source_path_ev_proxy_rebuild_{v_suffix}.json"
        elif key == "hypothesis_diversity":
            filename = f"source_path_hypothesis_diversity_{v_suffix}.json"
            
        path = reports_dir / filename
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
            
        # MD version
        md_path = path.with_suffix(".md")
        with open(md_path, "w") as f:
            f.write(f"# {key.replace('_', ' ').title()} - {version.upper()}\n\n")
            f.write("```json\n")
            f.write(json.dumps(data, indent=2))
            f.write("\n```\n")
