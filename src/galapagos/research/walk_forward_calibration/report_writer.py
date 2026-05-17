from __future__ import annotations

import json
import os
from typing import Any

import numpy as np
import pandas as pd


def write_v1_31_reports(
    results: dict[str, Any], 
    version: str = "v1.31", 
    output_dir: str = "reports/research"
) -> None:
    """
    Write V1.31 research reports.
    """
    os.makedirs(output_dir, exist_ok=True)
    v_suffix = version.replace(".", "_")
    
    def serialize(obj):
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        if isinstance(obj, (pd.Series, pd.Index)):
            return obj.tolist()
        if isinstance(obj, dict):
            return {str(k): serialize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [serialize(v) for v in obj]
        if hasattr(obj, "item") and callable(obj.item):
            # Handles numpy scalars like np.float64, np.bool_
            return obj.item()
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj

    for key, data in results.items():
        # Exception for recommendation: v1_31_recommendation
        base_name = f"{v_suffix}_{key}" if key == "recommendation" else f"{key}_{v_suffix}"
            
        json_path = os.path.join(output_dir, f"{base_name}.json")
        md_path = os.path.join(output_dir, f"{base_name}.md")
        
        serializable_data = serialize(data)
        
        with open(json_path, "w") as f:
            json.dump(serializable_data, f, indent=2)
            
        with open(md_path, "w") as f:
            f.write(f"# {key.replace('_', ' ').title()} - {version}\n\n")
            f.write("```json\n")
            f.write(json.dumps(serializable_data, indent=2))
            f.write("\n```\n")
