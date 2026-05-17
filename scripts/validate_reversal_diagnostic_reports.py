import argparse
import json
import os
from pathlib import Path

def validate_reversal_diagnostic_reports(version: str):
    v_suffix = version.replace(".", "_").lower()
    reports_dir = Path("reports/research")
    
    required_keys = [
        "selected_filter_rebuild",
        "period_comparison",
        "calibration_diagnostic",
        "ev_proxy_diagnostic",
        "payoff_diagnostic",
        "cost_drag_diagnostic",
        "score_distribution_shift",
        "feature_distribution_shift",
        "regime_diagnostic",
        "trade_concentration",
        "loss_decomposition",
        "summary",
        "source_snapshot"
    ]
    
    issues = []
    summary = {}
    
    # 1. Check existence
    for key in required_keys:
        filename = f"reversal_{key}_{v_suffix}.json"
        if key == "summary":
            filename = f"recent_reversal_diagnostic_summary_{v_suffix}.json"
            
        path = reports_dir / filename
        if not path.exists():
            issues.append(f"Missing report: {filename}")
        elif key == "summary":
            with open(path) as f:
                summary = json.load(f)

    # 2. Constraints Check
    if summary:
        if summary.get("evidence_classification") != "DIAGNOSTIC_ONLY":
            issues.append("evidence_classification must be DIAGNOSTIC_ONLY")
        if not summary.get("no_new_filter"):
            issues.append("no_new_filter must be true")
        if not summary.get("no_paper_live"):
            issues.append("no_paper_live must be true")
        if not summary.get("no_real_trading"):
            issues.append("no_real_trading must be true")
        if summary.get("holdout_executed"):
            issues.append("holdout_executed must be false")
        if summary.get("selected_filter") != "filter_ev_gt_cost_buffer":
            issues.append("selected_filter mismatch")
            
        # Ambiguity check
        for field in ["recent_2026_selected_count", "recent_2026_pnl"]:
            if field in summary:
                issues.append(f"Ambiguous field '{field}' found in summary")

        if not summary.get("source_count_match") and summary.get("rebuild_comparability_status") == "SELECTED_FILTER_REBUILD_SOURCE_UNAVAILABLE":
             issues.append("source_count_match is false and source reports unavailable")

    # 3. Project State Alignment
    state_path = Path("reports/PROJECT_STATE.json")
    if state_path.exists():
        with open(state_path) as f:
            state = json.load(f)
        
        # Ambiguity check
        for field in ["recent_2026_selected_count", "recent_2026_pnl"]:
            if field in state:
                issues.append(f"Ambiguous field '{field}' found in PROJECT_STATE")

        # Mandatory fields for V1.33.2
        checks = [
            ("version", version.upper()),
            ("final_verdict", summary.get("final_verdict")),
            ("primary_reversal_driver", summary.get("primary_reversal_driver")),
            ("rebuild_selected_count_2026", summary.get("rebuild_selected_count_2026")),
            ("rebuild_recent_2026_pnl", summary.get("rebuild_recent_2026_pnl")),
            ("source_v1_32_4_recent_2026_selected_count", summary.get("source_v1_32_4_recent_2026_selected_count")),
            ("source_v1_32_4_recent_2026_pnl", summary.get("source_v1_32_4_recent_2026_pnl")),
            ("source_count_match", summary.get("source_count_match")),
            ("rebuild_comparability_status", summary.get("rebuild_comparability_status")),
            ("consistency_check_status", "REVERSAL_DIAGNOSTIC_REPORTS_CONSISTENT_SOURCE_ALIGNED_DIAGNOSTIC_ONLY"),
            ("full_pytest_status", summary.get("full_pytest_status")),
            ("targeted_tests_status", summary.get("targeted_tests_status"))
        ]
        
        for field, expected in checks:
            if state.get(field) != expected:
                issues.append(f"PROJECT_STATE.{field} mismatch: expected {expected}, got {state.get(field)}")

    # 4. Source Snapshot Check
    snapshot_path = reports_dir / f"reversal_source_snapshot_{v_suffix}.json"
    if not snapshot_path.exists():
        issues.append("Missing source snapshot")

    # 5. Placeholder Check
    pkg_dir = Path("src/galapagos/research/reversal_diagnostic")
    for py_file in pkg_dir.glob("*.py"):
        with open(py_file) as f:
            content = f.read()
            if "TODO" in content or "FIXME" in content or "placeholder" in content.lower():
                issues.append(f"Placeholder found in {py_file.name}")

    # Final consistency report
    status = "REVERSAL_DIAGNOSTIC_REPORTS_CONSISTENT_SOURCE_ALIGNED_DIAGNOSTIC_ONLY" if not issues else "REVERSAL_DIAGNOSTIC_REPORTS_INCONSISTENT"
    
    result = {
        "status": status,
        "issues": issues,
        "version": version
    }
    
    consistency_path = reports_dir / f"reversal_diagnostic_consistency_check_{v_suffix}.json"
    with open(consistency_path, "w") as f:
        json.dump(result, f, indent=2)
        
    md_path = consistency_path.with_suffix(".md")
    with open(md_path, "w") as f:
        f.write(f"# Reversal Diagnostic Consistency Check - {version.upper()}\n\n")
        f.write(f"Status: **{status}**\n\n")
        if issues:
            f.write("## Issues\n")
            for issue in issues:
                f.write(f"- {issue}\n")
                
    print(f"Validation complete: {status}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    validate_reversal_diagnostic_reports(args.version)
