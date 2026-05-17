import argparse
import json
from pathlib import Path

def validate_reports(version):
    v_suffix = version.replace(".", "_").lower()
    reports_dir = Path("reports/research")
    
    mandatory_reports = [
        f"source_path_artifact_audit_{v_suffix}.json",
        f"source_path_code_inspection_{v_suffix}.json",
        f"source_path_candidate_hypotheses_{v_suffix}.json",
        f"source_path_replay_results_{v_suffix}.json",
        f"source_path_scorecard_{v_suffix}.json",
        f"source_path_match_analysis_{v_suffix}.json",
        f"source_path_non_reproducibility_classification_{v_suffix}.json",
        f"canonical_v1_32_4_selection_path_{v_suffix}.json",
        f"source_path_reconstruction_summary_{v_suffix}.json",
        f"{v_suffix}_recommendation.json"
    ]
    
    issues = []
    
    # 1. Exist check
    for report in mandatory_reports:
        if not (reports_dir / report).exists():
            issues.append(f"Missing mandatory report: {report}")
            
    if issues:
        return False, issues
        
    # 2. Content check
    summary_path = reports_dir / f"source_path_reconstruction_summary_{v_suffix}.json"
    with open(summary_path) as f:
        summary = json.load(f)
        
    if summary.get("evidence_classification") != "DIAGNOSTIC_ONLY":
        issues.append("evidence_classification must be DIAGNOSTIC_ONLY")
    if not summary.get("no_new_filter"):
        issues.append("no_new_filter must be true")
    if not summary.get("no_paper_live"):
        issues.append("no_paper_live must be true")
    if not summary.get("no_real_trading"):
        issues.append("no_real_trading must be true")
    if summary.get("target_source_count_2026") != 12691:
        issues.append(f"Target count mismatch: expected 12691, got {summary.get('target_source_count_2026')}")
        
    # V1.35.1 Strict Checks
    if summary.get("fallback_used_anywhere"):
        issues.append("fallback_used_anywhere must be false")
    if summary.get("artificial_probability_threshold_used_anywhere"):
        issues.append("artificial_probability_threshold_used_anywhere must be false")
        
    valid_ev_count = summary.get("valid_ev_replay_count", 0)
    verdict = summary.get("final_verdict")
    
    if verdict == "SOURCE_PATH_NOT_RECOVERED_RETIRE_AS_CANONICAL" and valid_ev_count == 0:
        issues.append("Final verdict retires source but zero valid EV replays were performed")
        
    # Replay consistency
    replays_path = reports_dir / f"source_path_replay_results_{v_suffix}.json"
    if replays_path.exists():
        with open(replays_path) as f:
            replays = json.load(f)
            for r in replays:
                if not r.get("ev_proxy_available") and r.get("total_count", 0) > 0:
                    issues.append(f"Replay {r.get('hypothesis_id')} has selected_count but EV proxy missing")
                    
    # Consistency check
    exact_recovered = summary.get("exact_source_path_recovered")
    path_status = summary.get("canonical_path_status")
    
    if exact_recovered and path_status != "CANONICAL_SOURCE_PATH_RECOVERED":
        issues.append("exact_source_path_recovered=True but status != CANONICAL_SOURCE_PATH_RECOVERED")
    if not exact_recovered and path_status == "CANONICAL_SOURCE_PATH_RECOVERED":
        issues.append("exact_source_path_recovered=False but status == CANONICAL_SOURCE_PATH_RECOVERED")
        
    if path_status == "CANONICAL_SOURCE_PATH_RECOVERED":
        if summary.get("best_source_match_count_2026") != 12691:
            issues.append("Canonical path recovered but count mismatch")
                    
    # Artifact status hardening
    audit_path = reports_dir / f"source_path_artifact_audit_{v_suffix}.json"
    if audit_path.exists():
        with open(audit_path) as f:
            audit = json.load(f)
            if audit.get("status") == "SOURCE_ARTIFACTS_FULLY_RECONSTRUCTABLE":
                if not audit.get("source_contains_selected_trade_ids") and not audit.get("source_contains_selected_timestamps"):
                    issues.append("Artifacts marked FULLY_RECONSTRUCTABLE without trade IDs or timestamps")
            
    # Recommendation check
    reco_path = reports_dir / f"{v_suffix}_recommendation.json"
    with open(reco_path) as f:
        reco = json.load(f)
        if exact_recovered:
            if "recovered canonical path" not in reco.get("recommended_next_step", "").lower():
                issues.append("Recommendation inconsistent with recovered path")
        else:
            if "retire" not in reco.get("recommended_next_step", "").lower():
                issues.append("Recommendation inconsistent with non-recovered path")

    # 3. Project State Alignment
    state_path = Path("reports/PROJECT_STATE.json")
    if state_path.exists():
        with open(state_path) as f:
            state = json.load(f)
            if state.get("version") != version.upper():
                issues.append("PROJECT_STATE version mismatch")
            if state.get("final_verdict") != summary.get("final_verdict"):
                issues.append(f"PROJECT_STATE verdict mismatch: {state.get('final_verdict')} vs {summary.get('final_verdict')}")
            
            # CRITICAL: Align consistency_check_status
            if version == "v1.35.2":
                expected_status = "SOURCE_PATH_RECONSTRUCTION_REPORTS_CONSISTENT_EV_REPLAY_STRICT_DIAGNOSTIC_ONLY"
                if state.get("consistency_check_status") != expected_status:
                    issues.append(f"PROJECT_STATE consistency_check_status must be {expected_status}")

    # 4. V1.35.2 Semantic Checks
    audit_status = summary.get("artifact_reconstructability_status")
    repro_status = summary.get("reproducibility_status")
    
    if audit_status != "SOURCE_ARTIFACTS_FULLY_RECONSTRUCTABLE" and repro_status == "NON_REPRODUCIBLE":
        issues.append("reproducibility_status must be more nuanced (NON_REPRODUCIBLE_WITH_AVAILABLE_ARTIFACTS) when artifacts are partial")
        
    primary_driver = summary.get("primary_non_reproducibility_driver")
    if primary_driver == "UNKNOWN_HISTORICAL_WARMUP_POLICY":
        # Check if warmup actually changes count
        replays_path = reports_dir / f"source_path_replay_results_{v_suffix}.json"
        if replays_path.exists():
            with open(replays_path) as f:
                replays = json.load(f)
                h2_count = next((r["count_2026"] for r in replays if r["hypothesis_id"] == "H2"), None)
                h3_count = next((r["count_2026"] for r in replays if r["hypothesis_id"] == "H3"), None)
                if h2_count == h3_count and h2_count is not None:
                    issues.append("UNKNOWN_HISTORICAL_WARMUP_POLICY cannot be primary driver if warmup/no-warmup counts are equal")

    if not summary.get("hypothesis_diversity_status"):
        issues.append("hypothesis_diversity_status is missing")
    else:
        # Strict diversity check: if dominant count = rebuild and freq >= 50%
        div_status = summary.get("hypothesis_diversity_status")
        rebuild_count = summary.get("rebuild_reference_count_2026")
        best_match_count = summary.get("best_source_match_count_2026")
        
        replays_path = reports_dir / f"source_path_replay_results_{v_suffix}.json"
        if replays_path.exists():
            with open(replays_path) as f:
                replays = json.load(f)
                counts = [r["count_2026"] for r in replays if r.get("replay_status") == "REPLAY_COMPLETE"]
                if counts:
                    from collections import Counter
                    freqs = Counter(counts)
                    dominant_count = freqs.most_common(1)[0][0]
                    dominant_freq = freqs.most_common(1)[0][1]
                    if dominant_count == rebuild_count and (dominant_freq / len(counts)) >= 0.5:
                        if div_status != "HYPOTHESES_COLLAPSE_TO_REBUILD_COUNT":
                            issues.append(f"hypothesis_diversity_status must be HYPOTHESES_COLLAPSE_TO_REBUILD_COUNT when dominant count matches rebuild ({rebuild_count}) with freq >= 50%")

    # 5. Current State Alignment
    latest_metrics_path = Path("reports/current/latest_metrics.json")
    if latest_metrics_path.exists():
        with open(latest_metrics_path) as f:
            latest = json.load(f)
            if latest.get("version") != summary.get("version", version.upper()):
                issues.append(f"latest_metrics.json version mismatch: {latest.get('version')} vs {version.upper()}")
            if latest.get("final_verdict") != summary.get("final_verdict"):
                issues.append("latest_metrics.json verdict mismatch")
            if latest.get("hypothesis_diversity_status") != summary.get("hypothesis_diversity_status"):
                issues.append("latest_metrics.json diversity status mismatch")

    latest_summary_path = Path("reports/current/latest_summary.md")
    if latest_summary_path.exists():
        with open(latest_summary_path) as f:
            content = f.read()
            if version.upper() not in content:
                issues.append(f"latest_summary.md does not mention version {version.upper()}")

    # 6. Safety Checks
    if summary.get("evidence_classification") != "DIAGNOSTIC_ONLY":
        issues.append("evidence_classification must be DIAGNOSTIC_ONLY")
    if summary.get("no_new_filter") is not True:
        issues.append("no_new_filter must be true")
    if summary.get("no_paper_live") is not True:
        issues.append("no_paper_live must be true")
    if summary.get("no_real_trading") is not True:
        issues.append("no_real_trading must be true")

    # Recommendation wording
    reco_path = reports_dir / f"{v_suffix}_recommendation.json"
    with open(reco_path) as f:
        reco = json.load(f)
        reco_text = reco.get("recommended_next_step", "").lower()
        if "unless historical selected-trade artifacts are recovered" not in reco_text:
            issues.append("Recommendation must mention historical artifacts recovery")
                
    if issues:
        return False, issues
        
    return True, []

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    
    success, issues = validate_reports(args.version)
    
    if success:
        v_suffix = args.version.replace(".", "_").lower()
        if args.version in ["v1.35.1", "v1.35.2", "v1.35.3"]:
            status = "SOURCE_PATH_RECONSTRUCTION_REPORTS_CONSISTENT_EV_REPLAY_STRICT_DIAGNOSTIC_ONLY"
        else:
            status = "SOURCE_PATH_RECONSTRUCTION_REPORTS_CONSISTENT_DIAGNOSTIC_ONLY"
            
        print(f"Validation complete: {status}")
        
        # Write validation report
        report = {
            "version": args.version,
            "status": status,
            "issues_found": []
        }
        with open(f"reports/research/source_path_reconstruction_consistency_check_{v_suffix}.json", "w") as f:
            json.dump(report, f, indent=2)
    else:
        print("Validation FAILED:")
        for issue in issues:
            print(f" - {issue}")
        exit(1)

if __name__ == "__main__":
    main()
