import json
import os
from pathlib import Path
from typing import Any

def serialize(obj):
    import numpy as np
    import pandas as pd
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    if isinstance(obj, (pd.Series, pd.Index)):
        return obj.tolist()
    if isinstance(obj, dict):
        return {str(k): serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize(v) for v in obj]
    if hasattr(obj, "item") and callable(obj.item):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj

def write_reversal_reports(
    results: dict[str, Any],
    version: str,
    output_dir: str = "reports/research"
):
    """
    Write all diagnostic reports.
    """
    os.makedirs(output_dir, exist_ok=True)
    v_suffix = version.replace(".", "_").lower()
    
    for key, payload in results.items():
        filename = f"reversal_{key}_{v_suffix}.json"
        if key == "summary":
            filename = f"recent_reversal_diagnostic_summary_{v_suffix}.json"
        elif key == "recommendation":
            filename = f"{v_suffix}_recommendation.json"
        elif key == "consistency":
            filename = f"reversal_diagnostic_consistency_check_{v_suffix}.json"
            
        path = Path(output_dir) / filename
        with open(path, "w") as f:
            json.dump(serialize(payload), f, indent=2)
            
        # MD version
        md_path = path.with_suffix(".md")
        with open(md_path, "w") as f:
            f.write(f"# {key.replace('_', ' ').title()} - {version.upper()}\n\n")
            f.write("```json\n")
            f.write(json.dumps(serialize(payload), indent=2))
            f.write("\n```\n")
