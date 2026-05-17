"""Validator for Galapagos V1.44 Regime-Aware Feature Set Reports."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

def is_finite(obj: Any) -> bool:
    """Recursively check if all numerical values are finite."""
    if isinstance(obj, dict):
        return all(is_finite(v) for v in obj.values())
    elif isinstance(obj, list):
        return all(is_finite(x) for x in obj)
    elif isinstance(obj, float):
        return not (obj != obj or obj == float('inf') or obj == float('-inf'))
    return True

def validate_v1_44_reports(version: str = "V1.44.4"):
    """Strict validation for V1.44.4 research reports."""
    
    v_slug = version.lower().replace(".", "_")
    report_path = Path(f"reports/research/regime_aware_feature_sets_{v_slug}.json")
    if not report_path.exists():
        return False, f"Main report missing: {report_path}"
        
    with open(report_path, "r", encoding="utf-8") as f:
        # Note: We read raw to check for NaN/Inf literals if any
        raw_content = f.read()
        if "NaN" in raw_content or "Infinity" in raw_content:
            return False, "JSON contains non-finite values (NaN/Infinity)"
        f.seek(0)
        data = json.load(f)
        
    errors = []
    
    # 1. Version Check
    if data.get("version") != version:
        errors.append(f"Version mismatch: {data.get('version')} vs {version}")
        
    # 2. Input Guard Check
    if not data.get("input_guard", {}).get("passed"):
        errors.append("Input Guard FAILED in report")
        
    # 3. Source Contract vs Verdict Honesty
    contract_passed = data.get("source_contract_passed", False)
    verdict = data.get("final_verdict", "")
    recommendation = data.get("recommended_next_step", "")
    metrics_available = data.get("metrics_available", False)
    
    if not contract_passed:
        if "PROMISING" in verdict:
            errors.append("Source Contract FAILED but verdict is PROMISING (Honesty violation)")
        if "fix source contract" not in recommendation.lower():
            errors.append("Source Contract FAILED but recommendation doesn't mention fixing it")
            
    if not metrics_available and "PROMISING" in verdict:
        errors.append("Metrics are NULL but verdict is PROMISING (Honesty violation)")
        
    if "preregistration" in recommendation.lower() or "preregister" in recommendation.lower():
        errors.append("Recommendation mentions preregistration (Forbidden in RESEARCH_ONLY)")
        
    if "v1.45" in recommendation.lower() or "v1_45" in recommendation.lower():
        errors.append("Recommendation mentions V1.45 (Premature)")
        
    # 4. Mandatory MD Reports
    mandatory_mds = [
        f"reports/research/regime_aware_feature_input_guard_{v_slug}.md",
        f"reports/research/regime_aware_feature_source_contract_{v_slug}.md",
        f"reports/research/regime_aware_feature_sets_{v_slug}.md",
        f"reports/research/regime_aware_feature_set_audit_{v_slug}.md",
        f"reports/research/regime_aware_feature_walk_forward_eval_{v_slug}.md",
        f"reports/research/regime_aware_feature_baseline_comparison_{v_slug}.md",
        f"reports/research/regime_aware_feature_temporal_robustness_{v_slug}.md",
        f"reports/research/regime_aware_feature_regime_robustness_{v_slug}.md",
        f"reports/research/regime_aware_feature_overfit_guard_{v_slug}.md",
        f"reports/research/regime_aware_feature_set_summary_{v_slug}.md",
        f"reports/research/regime_aware_feature_consistency_check_{v_slug}.md",
        f"reports/research/regime_aware_feature_global_zip_finiteness_audit_{v_slug}.md",
        f"reports/research/{v_slug}_recommendation.md",
        f"docs/regime_aware_feature_set_research_{v_slug}.md"
    ]
    for md in mandatory_mds:
        if not Path(md).exists():
            errors.append(f"Mandatory Markdown report missing: {md}")

    # 5. Global Zip Finiteness
    global_f_path = Path(f"reports/research/regime_aware_feature_global_zip_finiteness_audit_{v_slug}.json")
    if global_f_path.exists():
        with open(global_f_path, "r") as f:
            global_f = json.load(f)
            if not global_f.get("global_json_finiteness_passed"):
                errors.append("Global Zip Finiteness FAILED")
    else:
        errors.append("Global Zip Finiteness report missing")

    # 6. Safety Flags in latest_metrics
    latest_metrics_path = Path("reports/current/latest_metrics.json")
    if latest_metrics_path.exists():
        with open(latest_metrics_path, "r") as f:
            metrics = json.load(f)
            if metrics.get("version") != version:
                errors.append(f"latest_metrics version mismatch: {metrics.get('version')} vs {version}")
            for flag in ["no_strategy_validated", "no_paper_live", "no_real_trading", "no_preregistration_yet"]:
                if not metrics.get(flag, False):
                    errors.append(f"latest_metrics safety violation: {flag} must be True")
            if metrics.get("evidence_classification") not in ["RESEARCH_ONLY", "EXPLORATORY_ONLY"]:
                errors.append(f"Invalid evidence classification: {metrics.get('evidence_classification')}")
            if metrics.get("consistency_check_status") != "REGIME_AWARE_FEATURE_REPORTS_CONSISTENT_RESEARCH_ONLY":
                errors.append(f"Invalid consistency status in metrics: {metrics.get('consistency_check_status')}")
            if "RESEARCH_REPORTS" in metrics.get("consistency_check_status", ""):
                errors.append("Consistency status contains obsolete RESEARCH_REPORTS keyword")
                
            max_imp = metrics.get("improvement_vs_baseline_pct")
            if max_imp is not None and max_imp > 10000:
                errors.append(f"Explosive max_improvement_pct detected: {max_imp}")

    # 7. latest_summary.md check
    latest_summary_path = Path("reports/current/latest_summary.md")
    if latest_summary_path.exists():
        with open(latest_summary_path, "r", encoding="utf-8") as f:
            summary = f.read()
            if f"**Version**: {version}" not in summary:
                 errors.append(f"latest_summary version mismatch: {version} not found")
            if "Model Outputs Excluded: True" not in summary:
                 errors.append("latest_summary missing 'Model Outputs Excluded: True'")
            if "EV Proxies Excluded: True" not in summary:
                 errors.append("latest_summary missing 'EV Proxies Excluded: True'")
            if "Outcomes Excluded: True" not in summary:
                 errors.append("latest_summary missing 'Outcomes Excluded: True'")
            if "Audit Status: N/A" in summary:
                 errors.append("latest_summary contains 'Audit Status: N/A'")
            if "Total Sets Evaluated: 0" in summary:
                 errors.append("latest_summary contains 'Total Sets Evaluated: 0'")
            if "PROMISING" in summary:
                 errors.append("latest_summary contains forbidden PROMISING verdict")

    # 8. PROJECT_STATE checks
    state_json_path = Path("reports/PROJECT_STATE.json")
    if state_json_path.exists():
        with open(state_json_path, "r") as f:
            state = json.load(f)
            if state.get("version") != version:
                errors.append(f"PROJECT_STATE version mismatch: {state.get('version')} vs {version}")
            if "PROMISING" in state.get("final_verdict", ""):
                errors.append("PROJECT_STATE contains forbidden PROMISING verdict")
            if "preregistration" in state.get("recommended_next_step", "").lower():
                errors.append("PROJECT_STATE recommendation mentions preregistration")

    state_md_path = Path("reports/PROJECT_STATE.md")
    if state_md_path.exists():
        with open(state_md_path, "r", encoding="utf-8") as f:
            state_md = f.read()
            if f"# Project State - {version}" not in state_md:
                errors.append(f"PROJECT_STATE.md version mismatch: {version} not found in header")
            if "V1.43.4" in state_md.split("\n")[0]:
                errors.append("PROJECT_STATE.md still has V1.43.4 in header")

    if errors:
        return False, "\n".join(errors)
        
    return True, f"V1.44.4 validation PASSED for {version}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", type=str, default="V1.44.4")
    args = parser.parse_args()
    
    passed, msg = validate_v1_44_reports(args.version)
    print(msg)
    if not passed:
        exit(1)
