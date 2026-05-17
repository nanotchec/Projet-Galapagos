"""Validator for V1.45 research reports."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

def validate_reports(version_str: str) -> None:
    """Check for mandatory reports, finiteness, and state alignment."""
    
    root = Path.cwd()
    reports_dir = root / "reports/research"
    v_norm = version_str.replace(".", "_").lower()
    v_upper = version_str.upper()
    
    mandatory = [
        f"feature_ablation_input_guard_{v_norm}",
        f"feature_ablation_source_contract_{v_norm}",
        f"feature_ablation_family_registry_{v_norm}",
        f"feature_ablation_plan_{v_norm}",
        f"feature_ablation_results_{v_norm}",
        f"feature_permutation_importance_{v_norm}",
        f"feature_temporal_importance_{v_norm}",
        f"feature_regime_importance_{v_norm}",
        f"feature_ablation_stability_audit_{v_norm}",
        f"feature_ablation_leakage_safety_audit_{v_norm}",
        f"feature_ablation_baseline_comparison_{v_norm}",
        f"feature_importance_scorecard_{v_norm}",
        f"feature_ablation_importance_summary_{v_norm}",
        f"feature_ablation_importance_consistency_check_{v_norm}",
        f"{v_norm}_recommendation"
    ]
    
    issues = []
    
    # 1. Physical existence and Finitude
    all_reco_steps = []
    for name in mandatory:
        json_path = reports_dir / f"{name}.json"
        if not json_path.exists():
            issues.append(f"Missing mandatory report: {name}.json")
            continue
            
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            if not _check_finiteness(data):
                issues.append(f"Non-finite values detected in {name}.json")
            
            # Extract recommendations for cross-alignment check
            if "recommended_next_step" in data:
                all_reco_steps.append((name, data["recommended_next_step"]))

            # 2. Safety and Verdict checks in summary
            if name == f"feature_ablation_importance_summary_{v_norm}":
                if "VALIDATED" in data.get("final_verdict", ""):
                    issues.append("Forbidden verdict: final_verdict must not contain 'VALIDATED'")
                if not data.get("no_strategy_validated"):
                    issues.append("Safety violation: no_strategy_validated must be True")
                if not data.get("no_real_trading"):
                    issues.append("Safety violation: no_real_trading must be True")
                if data.get("holdout_executed"):
                    issues.append("Safety violation: holdout_executed must be False")
                if "preregister" in data.get("recommended_next_step", "").lower():
                    issues.append("Forbidden recommendation: do not mention preregistration")
                    
        except Exception as e:
            issues.append(f"Error parsing {name}.json: {str(e)}")

    # 3. State alignment
    project_state_json = root / "reports/PROJECT_STATE.json"
    if project_state_json.exists():
        state = json.loads(project_state_json.read_text(encoding="utf-8"))
        if state.get("version") != v_upper:
             issues.append(f"PROJECT_STATE version mismatch: {state.get('version')} (expected {v_upper})")
        
        if v_upper == "V1.45.1":
            if state.get("previous_base") == "V1.44.3":
                issues.append("PROJECT_STATE stale previous_base: V1.44.3 detected (expected V1.45)")
            if state.get("input_guard_status") == "REGIME_AWARE_FEATURE_INPUT_GUARD_PASSED":
                issues.append("PROJECT_STATE legacy input_guard_status detected")
            if state.get("source_contract_status") == "REGIME_AWARE_FEATURE_SOURCE_CONTRACT_PASSED":
                issues.append("PROJECT_STATE legacy source_contract_status detected")
            if "Regime-Aware Feature Set" in state.get("purpose", ""):
                issues.append("PROJECT_STATE legacy purpose detected")
            if state.get("status") == "RESEARCH_READY_BASELINE":
                issues.append("PROJECT_STATE legacy status RESEARCH_READY_BASELINE detected")
        
        if "recommended_next_step" in state:
            all_reco_steps.append(("PROJECT_STATE", state["recommended_next_step"]))

    # 4. Latest metrics alignment
    latest_metrics_json = root / "reports/current/latest_metrics.json"
    if latest_metrics_json.exists():
        latest = json.loads(latest_metrics_json.read_text(encoding="utf-8"))
        if latest.get("version") != v_upper:
            issues.append(f"latest_metrics version mismatch: {latest.get('version')}")
        if "recommended_next_step" in latest:
            all_reco_steps.append(("latest_metrics", latest["recommended_next_step"]))

    # 5. Recommendation Alignment
    if all_reco_steps:
        first_reco = all_reco_steps[0][1]
        for src, reco in all_reco_steps:
            if reco != first_reco:
                issues.append(f"Divergent recommendation in {src}: '{reco}' vs '{first_reco}'")

    # 6. Docs existence
    docs_path = root / f"docs/feature_ablation_importance_research_{v_norm}.md"
    if not docs_path.exists():
        issues.append(f"Missing documentation: {docs_path.name}")

    if issues:
        print(f"{v_upper} Validation FAILED:")
        for issue in issues:
            print(f"- {issue}")
        sys.exit(1)
    else:
        print(f"{v_upper} validation PASSED")

def _check_finiteness(obj: Any) -> bool:
    """Recursively check for NaN or Infinity in JSON-like structures."""
    if isinstance(obj, float):
        import math
        return math.isfinite(obj)
    if isinstance(obj, dict):
        return all(_check_finiteness(v) for v in obj.values())
    if isinstance(obj, list):
        return all(_check_finiteness(v) for v in obj)
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="V1.45")
    args = parser.parse_args()
    validate_reports(args.version)
