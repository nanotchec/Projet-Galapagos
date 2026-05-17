import json
from pathlib import Path

def load_v1_32_4_reports():
    reports_dir = Path("reports/research")
    reports = {}
    
    mapping = {
        "summary": "ev_net_research_summary_v1_32_4.json",
        "evaluation": "ev_filter_evaluation_v1_32_4.json",
        "temporal": "ev_filter_temporal_robustness_v1_32_4.json",
        "ev_proxy": "ev_proxy_build_v1_32_4.json",
        "candidate_grid": "ev_filter_candidate_grid_v1_32_4.json",
        "causal_safety": "ev_filter_causal_safety_audit_v1_32_4.json"
    }
    
    for key, filename in mapping.items():
        path = reports_dir / filename
        if path.exists():
            with open(path) as f:
                reports[key] = json.load(f)
        else:
            reports[key] = None
            
    return reports
