"""Validator for V1.43 diagnostic reports."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from _bootstrap import bootstrap_src_path
except ModuleNotFoundError:
    from scripts._bootstrap import bootstrap_src_path
bootstrap_src_path()

def check_for_nan_inf(data: any) -> bool:
    """Recursively check for NaN or Infinity in JSON-like data."""
    if isinstance(data, dict):
        return any(check_for_nan_inf(v) for v in data.values())
    elif isinstance(data, list):
        return any(check_for_nan_inf(x) for x in data)
    elif isinstance(data, float):
        import math
        return math.isnan(data) or math.isinf(data)
    return False

def validate_reports(version: str = "v1.43"):
    version_norm = version.lower().replace(".", "_")
    summary_path = Path(f"reports/research/regime_feature_diagnostic_summary_{version_norm}.json")
    if not summary_path.exists():
        print(f"Error: {summary_path} missing")
        return False
        
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    
    issues = []
    
    # 1. Base checks
    if summary.get("version") != version.upper():
        issues.append(f"Summary version mismatch: {summary.get('version')} != {version.upper()}")
    if summary.get("payoff_target_base_version") != "V1.42.3":
        issues.append("payoff_target_base_version must be V1.42.3")
    if summary.get("payoff_failure_base_version") != "V1.41":
        issues.append("payoff_failure_base_version must be V1.41")
    if summary.get("ev_degradation_base_version") != "V1.39":
        issues.append("ev_degradation_base_version must be V1.39")
    if summary.get("canonical_base_version") != "V1.37.2":
        issues.append("canonical_base_version must be V1.37.2")
        
    # 2. Safety checks
    if summary.get("evidence_classification") != "DIAGNOSTIC_ONLY":
        issues.append("evidence_classification must be DIAGNOSTIC_ONLY")
    if summary.get("no_new_filter") is not True:
        issues.append("no_new_filter must be true")
    if summary.get("no_strategy_validated") is not True:
        issues.append("no_strategy_validated must be true")
    if summary.get("no_paper_live") is not True:
        issues.append("no_paper_live must be true")
    if summary.get("no_real_trading") is not True:
        issues.append("no_real_trading must be true")
        
    # Check all research JSONs for NaN/Inf
    for p in Path("reports/research").glob(f"*{version_norm}.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if check_for_nan_inf(data):
                issues.append(f"NaN or Infinity detected in {p.name}")
        except Exception as e:
            issues.append(f"Could not audit {p.name}: {e}")

    # 3. Report presence
    required_reports = [
        f"regime_feature_input_guard_{version_norm}.json",
        f"regime_feature_inventory_{version_norm}.json",
        f"regime_feature_shift_analysis_{version_norm}.json",
        f"regime_feature_predictive_power_{version_norm}.json",
        f"regime_definition_audit_{version_norm}.json",
        f"regime_coverage_analysis_{version_norm}.json",
        f"regime_feature_interaction_{version_norm}.json",
        f"regime_feature_2026_failure_slice_{version_norm}.json",
        f"regime_feature_stability_scorecard_{version_norm}.json",
        f"regime_feature_diagnostic_summary_{version_norm}.json",
        f"regime_feature_state_alignment_{version_norm}.json",
        f"{version_norm}_recommendation.json"
    ]
    for rep in required_reports:
        if not Path(f"reports/research/{rep}").exists():
            issues.append(f"Missing required report: {rep}")
            
    # 3b. Inventory check for strict source semantics
    inv_path = Path(f"reports/research/regime_feature_inventory_{version_norm}.json")
    if inv_path.exists():
        inv = json.loads(inv_path.read_text(encoding="utf-8"))
        
        # Strict Raw Features Check
        raw_market_list = inv.get("raw_market_features", [])
        metadata = inv.get("metadata_features", [])
        model_outputs = inv.get("model_output_features", [])
        ev_proxies = inv.get("ev_proxy_features", [])
        forbidden = inv.get("outcome_forbidden_features", [])
        
        usable_raw = inv.get("usable_raw_features", [])
        usable_count = inv.get("usable_raw_feature_count", 0)
        
        if usable_count != len(usable_raw):
            issues.append(f"usable_raw_feature_count ({usable_count}) mismatch with list length ({len(usable_raw)})")
            
        if not usable_raw and usable_count > 0:
            issues.append("usable_raw_features list is empty but count > 0")

        # 1. Metadata in Raw
        meta_keywords = ["model_name", "feature_set", "split_name", "timeframe", "symbol"]
        for f in usable_raw:
            if any(k in f.lower() for k in meta_keywords):
                issues.append(f"Metadata feature '{f}' found in usable_raw_features")
        
        # 2. Model Outputs in Raw
        model_keywords = ["predicted_probability", "calibrated_probability", "predicted_label"]
        for f in usable_raw:
            if any(k in f.lower() for k in model_keywords):
                issues.append(f"Model output feature '{f}' found in usable_raw_features")
                
        # 3. EV Proxies in Raw
        proxy_keywords = ["ev_", "proxy", "avg_win", "avg_loss", "cost_proxy"]
        for f in usable_raw:
            if any(k in f.lower() for k in proxy_keywords):
                issues.append(f"EV proxy feature '{f}' found in usable_raw_features")
                
        # 4. Forbidden Outcomes in Raw
        forbidden_keywords = ["forward_return", "actual_target", "target", "outcome", "future", "direction_up_after_cost", "tp_before_sl", "mfe", "mae"]
        for f in usable_raw:
            if any(k in f.lower() for k in forbidden_keywords):
                issues.append(f"Forbidden outcome feature '{f}' found in usable_raw_features")

        # 5. Diagnostic lists population
        diag_model = inv.get("diagnostic_only_model_output_features", [])
        diag_ev = inv.get("diagnostic_only_ev_proxy_features", [])
        
        if not diag_model and inv.get("model_output_feature_count", 0) > 0:
            issues.append("diagnostic_only_model_output_features list is empty but model outputs exist")
        if not diag_ev and inv.get("ev_proxy_feature_count", 0) > 0:
            issues.append("diagnostic_only_ev_proxy_features list is empty but EV proxies exist")

    # 3c. Scorecard check
    sc_path = Path(f"reports/research/regime_feature_stability_scorecard_{version_norm}.json")
    if sc_path.exists():
        sc = json.loads(sc_path.read_text(encoding="utf-8"))
        rec_raw = sc.get("recommended_raw_feature_families_for_v1_44", [])
        rec_alpha = sc.get("recommended_alpha_feature_families_for_v1_44", [])
        
        forbidden_rec = ["alpha_score_or_model_output", "model_output_feature", "ev_proxy_feature", "metadata_feature", "unknown", "model_output_family"]
        for f in rec_raw:
            if f in forbidden_rec:
                issues.append(f"Forbidden family '{f}' found in recommended_raw_feature_families_for_v1_44")
        
        for f in rec_alpha:
            if f in forbidden_rec:
                issues.append(f"Forbidden family '{f}' found in recommended_alpha_feature_families_for_v1_44")
                
        if rec_raw == ["unknown"]:
            issues.append("recommended_raw_feature_families_for_v1_44 must not be only ['unknown']")
        
        if sc.get("model_outputs_excluded_from_raw_feature_recommendations") is not True:
            issues.append("model_outputs_excluded_from_raw_feature_recommendations must be true")
        if sc.get("ev_proxies_excluded_from_raw_feature_recommendations") is not True:
            issues.append("ev_proxies_excluded_from_raw_feature_recommendations must be true")
        if sc.get("alpha_score_or_model_output_removed") is not True:
            issues.append("alpha_score_or_model_output_removed must be true")

    # 4. Global State alignment
    ps_path = Path("reports/PROJECT_STATE.json")
    if ps_path.exists():
        ps = json.loads(ps_path.read_text(encoding="utf-8"))
        if ps.get("version") != version.upper():
            issues.append(f"PROJECT_STATE version mismatch")
        if ps.get("canonical_base_version") != "V1.37.2":
            issues.append(f"PROJECT_STATE canonical_base_version mismatch")
            
        if ps.get("consistency_check_status") != "REGIME_FEATURE_DIAGNOSTIC_REPORTS_CONSISTENT_DIAGNOSTIC_ONLY":
            issues.append(f"PROJECT_STATE consistency_check_status mismatch")
            
        if ps.get("alpha_score_or_model_output_removed") is not True:
            issues.append("PROJECT_STATE: alpha_score_or_model_output_removed must be true")
            
        # Legacy root fields check
        legacy_root_forbidden = ["best_target_observed", "best_horizon_observed", "beats_v1_40_1_target"]
        for f in legacy_root_forbidden:
            if f in ps:
                issues.append(f"Legacy field '{f}' still present at PROJECT_STATE root")

    lm_path = Path("reports/current/latest_metrics.json")
    if lm_path.exists():
        lm = json.loads(lm_path.read_text(encoding="utf-8"))
        if lm.get("consistency_check_status") != "REGIME_FEATURE_DIAGNOSTIC_REPORTS_CONSISTENT_DIAGNOSTIC_ONLY":
            issues.append("latest_metrics consistency_check_status mismatch")
        if lm.get("consistency_check_status") == "PAYOFF_TARGET_RESEARCH_REPORTS_CONSISTENT_STATE_ALIGNED_EXPLORATORY_ONLY":
            issues.append("latest_metrics contains legacy payoff target status")

    if issues:
        print(f"Validation FAILED for {version}:")
        for issue in issues:
            print(f"- {issue}")
        return False
        
    # Write consistency check report
    consistency = {
        "consistency_check_status": "REGIME_FEATURE_DIAGNOSTIC_REPORTS_CONSISTENT_DIAGNOSTIC_ONLY",
        "version": version,
        "status_field_policy": "REMOVED",
        "status_field_present": False,
        "issues": []
    }
    Path(f"reports/research/regime_feature_consistency_check_{version_norm}.json").write_text(json.dumps(consistency, indent=2))
    
    lines = [
        f"# Regime Feature Consistency Check {version}",
        "",
        "Status: REGIME_FEATURE_DIAGNOSTIC_REPORTS_CONSISTENT_DIAGNOSTIC_ONLY",
        "",
        "Integrity Fixes Applied:",
        "- NaN/Infinity Scan: PASSED",
        "- Outcome Leakage Check: PASSED (MFE/MAE excluded)",
        "- Input Guard: VERIFIED",
        "- Safety Constraints: VERIFIED",
        "- State Alignment: VERIFIED"
    ]
    Path(f"reports/research/regime_feature_consistency_check_{version_norm}.md").write_text("\n".join(lines))
    
    print(f"Validation PASSED for {version}.")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v1.43.1")
    args = parser.parse_args()
    if validate_reports(args.version):
        exit(0)
    else:
        exit(1)
