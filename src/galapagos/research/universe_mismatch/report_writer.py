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
    elif hasattr(obj, "to_dict"):
        return obj.to_dict()
    return obj

def write_reports(version, reports_data):
    v_suffix = version.replace(".", "_").lower()
    reports_dir = Path("reports/research")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    serialized_data = serialize(reports_data)
    
    for key, data in serialized_data.items():
        filename = f"universe_{key}_{v_suffix}.json"
        if key == "summary":
            filename = f"universe_mismatch_summary_{v_suffix}.json"
        elif key == "recommendation":
            filename = f"{v_suffix}_recommendation.json"
            
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

def generate_recommendation(version, summary):
    v_suffix = version.replace(".", "_").lower()
    return {
        "final_verdict": summary["final_verdict"],
        "recommended_next_step": summary["recommended_next_step"],
        "evidence_classification": "DIAGNOSTIC_ONLY",
        "no_new_filter": True,
        "no_paper_live": True,
        "no_money_deployment": True,
        "no_real_trading": True
    }
