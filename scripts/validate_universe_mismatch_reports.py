import argparse
import json
import os
from pathlib import Path

def validate_universe_mismatch_reports(version: str):
    v_suffix = version.replace(".", "_").lower()
    reports_dir = Path("reports/research")
    
    required_keys = [
        "source_report_audit",
        "timestamp_alignment",
        "duplicate_model_analysis",
        "join_path_audit",
        "warmup_policy_audit",
        "outcome_availability_audit",
        "filter_logic_replay",
        "count_reconciliation",
        "mismatch_classification",
        "summary"
    ]
    
    issues = []
    summary = {}
    
    # 1. Check existence
    for key in required_keys:
        filename = f"universe_{key}_{v_suffix}.json"
        if key == "summary":
            filename = f"universe_mismatch_summary_{v_suffix}.json"
            
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
        if summary.get("source_recent_2026_selected_count") != 12691:
            issues.append(f"Source count mismatch: expected 12691, got {summary.get('source_recent_2026_selected_count')}")

        # V1.34.1 Strict Replay Checks
        can_reconcile = summary.get("can_reconcile_source_count", False)
        any_matches_source = summary.get("any_path_matches_source", False)
        
        if can_reconcile and not any_matches_source:
            issues.append("can_reconcile_source_count is true but no path matches source count")
            
        if summary.get("count_reconciliation_status") == "COUNT_RECONCILIATION_COMPLETE_DELTA_EXPLAINED" and not any_matches_source:
            issues.append("Reconciliation status is COMPLETE but no path matches source count")
            
        if summary.get("final_verdict") == "UNIVERSE_MISMATCH_RESOLVED" and not any_matches_source:
            issues.append("Verdict is RESOLVED but source count not replayed")

        # Waterfall Inconsistency check
        recon_path = reports_dir / f"universe_count_reconciliation_{v_suffix}.json"
        if recon_path.exists():
            with open(recon_path) as f:
                recon = json.load(f)
                for step in recon:
                    if step["step_name"] == "after_timestamp_alignment" and step["count_2026"] == 0:
                        if summary.get("timestamp_alignment_status") == "TIMESTAMP_ALIGNMENT_OK":
                            issues.append("Waterfall inconsistency: count_2026 is 0 after alignment while status is OK")

    # 3. Project State Alignment
    state_path = Path("reports/PROJECT_STATE.json")
    if state_path.exists():
        with open(state_path) as f:
            state = json.load(f)
        
        checks = [
            ("version", version.upper()),
            ("final_verdict", summary.get("final_verdict")),
            ("primary_mismatch_driver", summary.get("primary_mismatch_driver")),
            ("source_recent_2026_selected_count", summary.get("source_recent_2026_selected_count")),
            ("rebuild_recent_2026_selected_count", summary.get("rebuild_recent_2026_selected_count")),
            ("any_path_matches_source", summary.get("any_path_matches_source")),
            ("duplicate_policy_explains_exact_delta", summary.get("duplicate_policy_explains_exact_delta")),
            ("consistency_check_status", "UNIVERSE_MISMATCH_REPORTS_CONSISTENT_DIAGNOSTIC_ONLY")
        ]
        
        for field, expected in checks:
            if state.get(field) != expected:
                issues.append(f"PROJECT_STATE.{field} mismatch: expected {expected}, got {state.get(field)}")

    # Final consistency report
    status = "UNIVERSE_MISMATCH_REPORTS_CONSISTENT_DIAGNOSTIC_ONLY" if not issues else "UNIVERSE_MISMATCH_REPORTS_INCONSISTENT"
    
    result = {
        "status": status,
        "issues": issues,
        "version": version
    }
    
    consistency_path = reports_dir / f"universe_mismatch_consistency_check_{v_suffix}.json"
    with open(consistency_path, "w") as f:
        json.dump(result, f, indent=2)
        
    md_path = consistency_path.with_suffix(".md")
    with open(md_path, "w") as f:
        f.write(f"# Universe Mismatch Consistency Check - {version.upper()}\n\n")
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
    validate_universe_mismatch_reports(args.version)
