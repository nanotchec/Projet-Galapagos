"""Write V1.43 diagnostic reports."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

def write_v1_43_reports(results: dict[str, Any], version: str = "v1.43"):
    """Write all JSON and MD reports for V1.43."""
    version_norm = version.lower().replace(".", "_")
    output_dir = Path("reports/research")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # List of report keys and their file basenames
    report_map = {
        "input_guard": "regime_feature_input_guard",
        "feature_inventory": "regime_feature_inventory",
        "feature_shift": "regime_feature_shift_analysis",
        "predictive_power": "regime_feature_predictive_power",
        "regime_definition": "regime_definition_audit",
        "regime_coverage": "regime_coverage_analysis",
        "regime_feature_interaction": "regime_feature_interaction",
        "failure_slice": "regime_feature_2026_failure_slice",
        "stability_scorecard": "regime_feature_stability_scorecard",
        "verdict": "regime_feature_diagnostic_summary",
        "state_alignment": "regime_feature_state_alignment",
        "recommendation": "v1_43_recommendation"
    }
    
    for key, base_name in report_map.items():
        data = results[key]
        if key == "recommendation":
             file_path = output_dir / f"{version_norm}_recommendation.json"
        else:
             file_path = output_dir / f"{base_name}_{version_norm}.json"
             
        file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        
        # Write basic MD
        md_path = file_path.with_suffix(".md")
        lines = [
            f"# {base_name.replace('_', ' ').title()} {version.upper()}",
            "",
            f"Status: {data.get(key + '_status', 'COMPLETE')}",
            "",
            "### Summary",
            f"```json\n{json.dumps(data, indent=2)}\n```"
        ]
        if key == "verdict":
             lines[2] = f"Verdict: **{data['final_verdict']}**"
        
        md_path.write_text("\n".join(lines), encoding="utf-8")
        
    print(f"All V1.43 reports written to {output_dir}")
