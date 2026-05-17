from __future__ import annotations

import json
import os
from typing import Any


def write_v1_30_reports(
    results: dict[str, Any], 
    version: str = "v1.30",
    output_dir: str = "reports/research"
):
    """
    Write all research reports with a version suffix.
    """
    os.makedirs(output_dir, exist_ok=True)
    v_suffix = version.replace(".", "_")
    
    for key, data in results.items():
        base_name = f"{v_suffix}_{key}" if key == "recommendation" else f"{key}_{v_suffix}"
            
        # JSON
        json_path = os.path.join(output_dir, f"{base_name}.json")
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)
            
        # MD
        md_path = os.path.join(output_dir, f"{base_name}.md")
        with open(md_path, "w") as f:
            title = key.replace("_", " ").title()
            f.write(f"# {title} - Galapagos {version}\n\n")
            f.write("## Status\n")
            status = (
                data.get("point_in_time_status") 
                or data.get("integrity_status") 
                or data.get("status") 
                or data.get("cost_model_status") 
                or data.get("ev_proxy_status")
                or data.get("final_verdict")
            )
            f.write(f"- **{status}**\n\n")
            f.write("## Details\n")
            f.write("```json\n")
            f.write(json.dumps(data, indent=2))
            f.write("\n```\n")
