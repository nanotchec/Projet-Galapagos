"""Report writer for V1.44 research."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

def sanitize_finite(obj: Any) -> Any:
    """Recursively replace NaN/Inf/-Inf with None for JSON compliance."""
    if isinstance(obj, dict):
        return {k: sanitize_finite(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_finite(x) for x in obj]
    elif isinstance(obj, float):
        if obj != obj or obj == float('inf') or obj == float('-inf'):
            return None
    return obj

def save_json_report(data: dict[str, Any], file_path: str):
    """Save a dictionary as a JSON report, ensuring all values are finite."""
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    sanitized_data = sanitize_finite(data)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(sanitized_data, f, indent=2)

def generate_markdown_summary(
    results: dict[str, Any],
    file_path: str
):
    """Generate a markdown summary of the research results."""
    lines = [
        f"# Galapagos V1.44 Research Summary: Regime-Aware Feature Sets",
        f"",
        f"**Version**: {results.get('version', 'V1.44')}",
        f"**Status**: {results.get('status', 'N/A')}",
        f"**Final Verdict**: {results.get('final_verdict', 'N/A')}",
        f"**Evidence Classification**: {results.get('evidence_classification', 'RESEARCH_ONLY')}",
        f"",
        f"## Feature Set Audit Results",
        f"- Total Sets Evaluated: {len(results.get('feature_sets', []))}",
        f"- Audit Status: {results.get('audit_status', 'N/A')}",
        f"",
        f"## Walk-Forward Evaluation Results",
        f"- Evaluation Period: {results.get('eval_period', 'N/A')}",
        f"- Best Feature Set (Exploratory): {results.get('best_feature_set', 'N/A')}",
        f"- Stability Score (Median): {results.get('median_stability_score', 'N/A')}",
        f"",
        f"## Safety & Compliance",
        f"- Model Outputs Excluded: {results.get('model_outputs_excluded', False)}",
        f"- EV Proxies Excluded: {results.get('ev_proxies_excluded', False)}",
        f"- Outcomes Excluded: {results.get('outcomes_excluded', False)}",
        f"- No Real Trading: {results.get('no_real_trading', True)}",
        f"- No Strategy Validated: {results.get('no_strategy_validated', True)}",
        f"",
        f"## Next Steps",
        f"{results.get('next_steps', 'Continue research')}"
    ]
    
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
