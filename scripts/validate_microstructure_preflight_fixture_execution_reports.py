import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    v_norm = args.version.replace(".", "_").lower()
    root = Path(__file__).parent.parent
    reports_dir = root / "reports/research"
    
    summary_path = reports_dir / f"microstructure_preflight_fixture_summary_{v_norm}.json"
    recommendation_path = reports_dir / f"{v_norm}_recommendation.json"
    consistency_path = reports_dir / f"microstructure_preflight_fixture_consistency_check_{v_norm}.json"
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

    # 3. Alignment of key flags
    flags = [
        "preflight_skeleton_fixture_execution_passed",
        "controlled_collection_readiness_plan_created",
        "recommended_next_step",
        "next_allowed_phase"
    ]
    for flag in flags:
        vals = [
            summary.get(flag),
            recommendation.get(flag),
            project_state.get(flag),
            latest_metrics.get(flag)
        ]
        if len(set(vals)) > 1:
            print(f"ERROR: Flag mismatch for {flag}: {vals}")
            sys.exit(1)

    # 4. Strict Safety Checks
    if summary.get("preflight_skeleton_fixture_execution") is not True:
        print("ERROR: preflight_skeleton_fixture_execution must be true")
        sys.exit(1)

    if summary.get("preflight_skeleton_executed") is not True:
        print("ERROR: preflight_skeleton_executed must be true")
        sys.exit(1)

    forbidden_true = [
        "preflight_real_execution", "real_preflight_executed",
        "controlled_collection_executed", "real_collection_approved",
        "network_enabled", "external_api_called", "external_data_downloaded",
        "new_data_files_created", "parquet_created", "csv_created",
        "sqlite_created", "jsonl_created", "db_created",
        "manifest_data_file_created", "controlled_local_preflight_executed",
        "no_strategy_validated" # Wait, no_strategy_validated should be True
    ]
    # Correcting logic for "must be false" fields
    must_be_false = [
        "preflight_real_execution", "real_preflight_executed",
        "controlled_collection_executed", "real_collection_approved",
        "network_enabled", "external_api_called", "external_data_downloaded",
        "new_data_files_created", "parquet_created", "csv_created",
        "sqlite_created", "jsonl_created", "db_created",
        "manifest_data_file_created", "controlled_local_preflight_executed",
        "holdout_executed", "codex_cli_called", "real_orders_possible"
    ]
    for field in must_be_false:
        if summary.get(field) is True:
            print(f"ERROR: {field} must be false in summary")
            sys.exit(1)

    must_be_true = [
        "preflight_skeleton_fixture_execution", "preflight_skeleton_executed",
        "network_gate_enabled", "write_gate_enabled",
        "network_gate_runtime_checked", "write_gate_runtime_checked",
        "network_disabled", "network_disabled_by_default",
        "future_network_activation_requires_separate_approval",
        "human_review_required_before_collection", "dry_run_only",
        "local_fixture_only", "fixture_only", "synthetic_or_minimal_sample",
        "not_for_research_results", "simulated_requests_allowed",
        "no_data_directory_writes", "manifest_preview_generated",
        "normalized_records_preview_generated", "timestamp_causality_runtime_checked",
        "no_lookahead_confirmed", "no_new_filter", "no_strategy_validated",
        "no_preregistration_yet", "no_paper_live", "no_real_trading"
    ]
    for field in must_be_true:
        if summary.get(field) is not True:
            print(f"ERROR: {field} must be true in summary")
            sys.exit(1)

    if summary.get("requests_executed_count", 0) != 0:
        print("ERROR: requests_executed_count must be 0")
        sys.exit(1)

    # 5. Verdict specific checks
    v = summary.get("final_verdict", "")
    passed = summary.get("preflight_skeleton_fixture_execution_passed")
    if passed:
        if v != "MICROSTRUCTURE_PREFLIGHT_SKELETON_FIXTURE_EXECUTION_PASSED":
            print("ERROR: Inconsistent verdict for passed execution")
            sys.exit(1)
        if summary.get("next_allowed_phase") != "controlled_collection_readiness_review":
            print("ERROR: Inconsistent next_allowed_phase for passed execution")
            sys.exit(1)
        if "review controlled collection readiness plan" not in summary.get("recommended_next_step", "").lower():
            print("ERROR: Inconsistent recommendation for passed execution")
            sys.exit(1)
    else:
        if v != "MICROSTRUCTURE_PREFLIGHT_SKELETON_FIXTURE_EXECUTION_INCOMPLETE":
            print("ERROR: Inconsistent verdict for incomplete execution")
            sys.exit(1)
        if summary.get("next_allowed_phase") != "more_preflight_skeleton_fixture_hardening":
            print("ERROR: Inconsistent next_allowed_phase for incomplete execution")
            sys.exit(1)
        if "continue preflight skeleton fixture hardening" not in summary.get("recommended_next_step", "").lower():
            print("ERROR: Inconsistent recommendation for incomplete execution")
            sys.exit(1)

    # 6. Consistency report specific
    if consistency.get("consistency_check_status") != "MICROSTRUCTURE_PREFLIGHT_FIXTURE_REPORTS_CONSISTENT_INFRASTRUCTURE_ONLY":
        print("ERROR: Consistency check status incorrect")
        sys.exit(1)
    if consistency.get("issues") != []:
        print("ERROR: Consistency issues found")
        sys.exit(1)

    # 7. Required files
    required_stems = [
        "microstructure_preflight_fixture_input_guard",
        "microstructure_preflight_fixture_executor",
        "microstructure_preflight_fixture_execution_review",
        "microstructure_network_gate_runtime_audit",
        "microstructure_write_gate_runtime_audit",
        "microstructure_manifest_preview_runtime_audit",
        "microstructure_normalized_record_runtime_audit",
        "microstructure_timestamp_causality_runtime_audit",
        "microstructure_skeleton_hardening_runtime_review",
        "microstructure_controlled_collection_readiness_plan",
        "microstructure_preflight_fixture_decision",
        "microstructure_preflight_fixture_recommendation",
        "microstructure_preflight_fixture_summary",
        "microstructure_preflight_fixture_consistency_check",
    ]
    for stem in required_stems:
        if not (reports_dir / f"{stem}_{v_norm}.json").exists():
            print(f"ERROR: Missing JSON report {stem}")
            sys.exit(1)
        if not (reports_dir / f"{stem}_{v_norm}.md").exists():
            print(f"ERROR: Missing MD report {stem}")
            sys.exit(1)

    if not (root / f"docs/microstructure_preflight_fixture_execution_{v_norm}.md").exists():
        print("ERROR: Missing final documentation MD")
        sys.exit(1)

    print(f"SUCCESS: Preflight fixture execution validation passed for {args.version}")

if __name__ == "__main__":
    main()
