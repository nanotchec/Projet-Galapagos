"""Validator for microstructure regime diagnostic reports V1.49.1."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"FAILED: Could not load JSON from {path}: {e}")
        sys.exit(1)

def check_finiteness(obj: Any) -> bool:
    if isinstance(obj, dict):
        return all(check_finiteness(v) for v in obj.values())
    if isinstance(obj, list):
        return all(check_finiteness(v) for v in obj)
    if isinstance(obj, float):
        return not (obj != obj or obj == float('inf') or obj == float('-inf'))
    return True

def main():
    parser = argparse.ArgumentParser(description="Validate V1.49.1 Reports")
    parser.add_argument("--version", default="v1.49.1")
    args = parser.parse_args()
    
    version_norm = args.version.lower().replace(".", "_")
    base_path = Path(__file__).parents[1]
    report_base = base_path / "reports/research"
    docs_path = base_path / "docs"
    
    # Required reports (JSON + MD)
    required_json = [
        f"micro_regime_diagnostic_input_guard_{version_norm}.json",
        f"micro_regime_label_load_report_{version_norm}.json",
        f"micro_regime_slice_report_{version_norm}.json",
        f"micro_regime_loss_decomposition_{version_norm}.json",
        f"micro_regime_feature_interaction_{version_norm}.json",
        f"micro_regime_temporal_stability_{version_norm}.json",
        f"micro_regime_separability_eval_{version_norm}.json",
        f"micro_regime_transition_eval_{version_norm}.json",
        f"micro_regime_2026_failure_explanation_{version_norm}.json",
        f"micro_regime_comparison_to_previous_{version_norm}.json",
        f"micro_regime_causal_availability_audit_{version_norm}.json",
        f"micro_regime_recommendation_{version_norm}.json",
        f"micro_regime_diagnostic_summary_{version_norm}.json",
        f"micro_regime_diagnostic_consistency_check_{version_norm}.json",
        f"{version_norm}_recommendation.json",
    ]
    
    required_md = [r.replace(".json", ".md") for r in required_json]
    required_md.append(f"docs/microstructure_regime_diagnostic_{version_norm}.md")

    # Check existence
    missing = []
    for r in required_json:
        if not (report_base / r).exists():
            missing.append(f"reports/research/{r}")
    for r in required_md:
        if r.startswith("docs/"):
            if not (base_path / r).exists():
                missing.append(r)
        else:
            if not (report_base / r).exists():
                missing.append(f"reports/research/{r}")
    
    if missing:
        print(f"FAILED: Missing required reports: {missing}")
        sys.exit(1)
        
    # Consistency check content
    consistency = load_json(report_base / f"micro_regime_diagnostic_consistency_check_{version_norm}.json")
    if consistency.get("version") != "V1.49.1":
        print(f"FAILED: Consistency check version mismatch: expected V1.49.1, got {consistency.get('version')}")
        sys.exit(1)
    if consistency.get("previous_base") != "V1.49":
        print(f"FAILED: Consistency check previous_base mismatch: expected V1.49, got {consistency.get('previous_base')}")
        sys.exit(1)
    if consistency.get("issues") != []:
        print(f"FAILED: Consistency check has issues: {consistency.get('issues')}")
        sys.exit(1)
    if consistency.get("consistency_check_status") != "MICRO_REGIME_DIAGNOSTIC_REPORTS_CONSISTENT_RESEARCH_ONLY":
        print(f"FAILED: Consistency check status mismatch: {consistency.get('consistency_check_status')}")
        sys.exit(1)
    if not consistency.get("required_reports_present"):
        print("FAILED: Consistency check says required_reports_present is false")
        sys.exit(1)
    if not consistency.get("required_markdown_reports_present"):
        print("FAILED: Consistency check says required_markdown_reports_present is false")
        sys.exit(1)

    # Safety flags
    expected_safety = {
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "codex_cli_called": False,
        "real_orders_possible": False
    }
    
    summary = load_json(report_base / f"micro_regime_diagnostic_summary_{version_norm}.json")
    for k, v in expected_safety.items():
        if summary.get(k) != v:
            print(f"FAILED: Safety flag mismatch in summary for {k}: expected {v}, got {summary.get(k)}")
            sys.exit(1)
    
    rec_file = f"{version_norm}_recommendation.json"
    recommendation = load_json(report_base / rec_file)
    for k, v in expected_safety.items():
        if recommendation.get(k) != v:
            print(f"FAILED: Safety flag mismatch in recommendation for {k}: expected {v}, got {recommendation.get(k)}")
            sys.exit(1)

    # State alignment checks
    project_state = load_json(base_path / "reports/PROJECT_STATE.json")
    latest_metrics = load_json(base_path / "reports/current/latest_metrics.json")
    
    for state_doc in [project_state, latest_metrics]:
        if state_doc.get("version") != "V1.49.1":
            print(f"FAILED: State version mismatch: expected V1.49.1, got {state_doc.get('version')}")
            sys.exit(1)
        if state_doc.get("final_verdict") != "MICRO_REGIME_DIAGNOSTIC_ACTIONABLE_BUT_UNVALIDATED":
            print(f"FAILED: State final_verdict mismatch: {state_doc.get('final_verdict')}")
            sys.exit(1)
        if state_doc.get("recommended_next_step") != "improve microstructure data coverage before further regime diagnostics":
            print(f"FAILED: State recommended_next_step mismatch: {state_doc.get('recommended_next_step')}")
            sys.exit(1)
        # Check for old V1.48.1 strings just in case
        if "rerun regime diagnostics" in state_doc.get("recommended_next_step", "").lower():
            print("FAILED: State contains old V1.48.1 recommendation")
            sys.exit(1)
        if "MICROSTRUCTURE_REGIME_LABELS" in state_doc.get("final_verdict", ""):
            print("FAILED: State contains old V1.48.1 verdict prefix")
            sys.exit(1)

    # Forbidden strings check
    verdict = summary.get("final_verdict", "")
    if "VALIDATED" in verdict and "UNVALIDATED" not in verdict:
        print("FAILED: Final verdict cannot contain VALIDATED")
        sys.exit(1)
        
    forbidden_rec = ["preregistration", "paper live", "real trading"]
    rec = summary.get("recommended_next_step", "").lower()
    if any(f in rec for f in forbidden_rec):
        print(f"FAILED: Forbidden next step in summary: {rec}")
        sys.exit(1)
        
    # Finiteness
    for r in required_json:
        data = load_json(report_base / r)
        if not check_finiteness(data):
            print(f"FAILED: NaN or Infinity detected in {r}")
            sys.exit(1)
            
    print("VALIDATION PASSED")

if __name__ == "__main__":
    main()
