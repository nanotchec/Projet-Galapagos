import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    v_norm = args.version.replace(".", "_").lower()
    root = Path(__file__).parent.parent
    reports_dir = root / "reports/research"
    
    summary_path = reports_dir / f"microstructure_preflight_skeleton_summary_{v_norm}.json"
    recommendation_path = reports_dir / f"v_norm_recommendation.json".replace("v_norm", v_norm)
    consistency_path = reports_dir / f"microstructure_preflight_skeleton_consistency_check_{v_norm}.json"
    project_state_path = root / "reports/PROJECT_STATE.json"
    latest_metrics_path = root / "reports/current/latest_metrics.json"

    paths = [summary_path, recommendation_path, consistency_path, project_state_path, latest_metrics_path]
    for p in paths:
        if not p.exists():
            print(f"ERROR: Missing required file {p}")
            sys.exit(1)

    def load_json(p: Path) -> Dict[str, Any]:
        with open(p) as f:
            data = json.load(f)
            # Check for NaN/Infinity
            json_str = json.dumps(data)
            if "NaN" in json_str or "Infinity" in json_str:
                print(f"ERROR: NaN or Infinity found in {p}")
                sys.exit(1)
            return data

    summary = load_json(summary_path)
    recommendation = load_json(recommendation_path)
    consistency = load_json(consistency_path)
    project_state = load_json(project_state_path)
    latest_metrics = load_json(latest_metrics_path)

    # 1. Version Check
    expected_v = args.version.upper()
    for d, p in [(summary, summary_path), (recommendation, recommendation_path), (consistency, consistency_path), (project_state, project_state_path), (latest_metrics, latest_metrics_path)]:
        if d.get("version") != expected_v:
            print(f"ERROR: Version mismatch in {p}: expected {expected_v}, got {d.get('version')}")
            sys.exit(1)

    # 2. Verdict Alignment
    verdicts = [
        summary.get("final_verdict"),
        recommendation.get("final_verdict"),
        project_state.get("final_verdict"),
        latest_metrics.get("final_metrics", {}).get("final_verdict") if "final_metrics" in latest_metrics else latest_metrics.get("final_verdict")
    ]
    if len(set(verdicts)) > 1:
        print(f"ERROR: Verdict mismatch: {verdicts}")
        sys.exit(1)

    # 3. Skeleton Created Alignment
    skeletons = [
        summary.get("preflight_skeleton_created"),
        recommendation.get("preflight_skeleton_created"),
        project_state.get("preflight_skeleton_created"),
        latest_metrics.get("preflight_skeleton_created")
    ]
    if len(set(skeletons)) > 1:
        print(f"ERROR: preflight_skeleton_created mismatch: {skeletons}")
        sys.exit(1)

    # 4. Strict Safety Checks
    forbidden_true = [
        "network_enabled", "real_collection_approved", "real_collection_executed",
        "preflight_skeleton_executed", "preflight_real_execution", "wrapper_real_execution",
        "wrapper_executed", "controlled_local_preflight_executed", "real_preflight_executed",
        "parquet_created", "csv_created", "sqlite_created", "jsonl_created", "db_created",
        "manifest_data_file_created", "holdout_executed", "codex_cli_called", "real_orders_possible"
    ]
    for field in forbidden_true:
        if summary.get(field) is True:
            print(f"ERROR: {field} must be false in summary")
            sys.exit(1)
        if project_state.get(field) is True:
            print(f"ERROR: {field} must be false in PROJECT_STATE")
            sys.exit(1)

    if summary.get("requests_executed_count", 0) != 0:
        print("ERROR: requests_executed_count must be 0")
        sys.exit(1)

    if summary.get("evidence_classification") != "INFRASTRUCTURE_ONLY":
        print("ERROR: evidence_classification must be INFRASTRUCTURE_ONLY")
        sys.exit(1)

    if summary.get("consistency_check_status") != "MICROSTRUCTURE_PREFLIGHT_SKELETON_REPORTS_CONSISTENT_INFRASTRUCTURE_ONLY":
        print("ERROR: consistency_check_status incorrect")
        sys.exit(1)

    # 5. Recommendation Checks
    rec_step = summary.get("recommended_next_step", "")
    forbidden_words = ["real collection", "live collection", "paper live", "real trading", "preregistration", "enable network now"]
    for word in forbidden_words:
        if word in rec_step.lower():
            print(f"ERROR: Forbidden word '{word}' in recommended_next_step")
            sys.exit(1)

    if summary.get("preflight_skeleton_created"):
        if summary.get("next_allowed_phase") != "network_disabled_preflight_skeleton_fixture_execution":
            print("ERROR: next_allowed_phase mismatch for skeleton created")
            sys.exit(1)
        if "execute network-disabled preflight skeleton on local fixtures only" not in rec_step.lower():
            print("ERROR: recommended_next_step mismatch for skeleton created")
            sys.exit(1)

    # 6. Verdict Content Checks
    v = summary.get("final_verdict", "")
    forbidden_verdicts = ["VALIDATED", "REAL_COLLECTION_APPROVED", "NETWORK_ENABLED", "REAL_PREFLIGHT_EXECUTED"]
    for fv in forbidden_verdicts:
        if fv in v:
            print(f"ERROR: Forbidden string '{fv}' in final_verdict")
            sys.exit(1)

    # 7. Consistency Report Check
    if consistency.get("consistency_check_status") != "MICROSTRUCTURE_PREFLIGHT_SKELETON_REPORTS_CONSISTENT_INFRASTRUCTURE_ONLY":
        print("ERROR: Consistency check status incorrect")
        sys.exit(1)
    if consistency.get("issues") != []:
        print("ERROR: Consistency issues found")
        sys.exit(1)

    # 8. Report Presence
    required_stems = [
        "microstructure_preflight_skeleton_input_guard",
        "microstructure_wrapper_fixture_review",
        "microstructure_wrapper_hardening_review",
        "microstructure_aggressive_network_safety_tests",
        "microstructure_aggressive_write_safety_tests",
        "microstructure_preflight_skeleton_contract",
        "microstructure_preflight_skeleton_builder",
        "microstructure_preflight_skeleton_safety_policy",
        "microstructure_preflight_skeleton_manifest_preview",
        "microstructure_preflight_skeleton_test_plan",
        "microstructure_preflight_skeleton_decision",
        "microstructure_preflight_skeleton_recommendation",
        "microstructure_preflight_skeleton_summary",
        "microstructure_preflight_skeleton_consistency_check",
    ]
    for stem in required_stems:
        if not (reports_dir / f"{stem}_{v_norm}.json").exists():
            print(f"ERROR: Missing JSON report {stem}")
            sys.exit(1)
        if not (reports_dir / f"{stem}_{v_norm}.md").exists():
            print(f"ERROR: Missing MD report {stem}")
            sys.exit(1)

    if not (root / f"docs/microstructure_preflight_skeleton_{v_norm}.md").exists():
        print("ERROR: Missing final documentation MD")
        sys.exit(1)

    print(f"SUCCESS: Preflight skeleton validation passed for {args.version}")

if __name__ == "__main__":
    main()
