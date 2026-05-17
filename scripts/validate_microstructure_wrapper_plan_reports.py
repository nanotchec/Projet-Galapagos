import argparse
import json
import math
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    # V1.63.2 Specific Hardening
    if args.version != "V1.63.2":
        print(f"ERROR: Validator expects V1.63.2, got {args.version}")
        sys.exit(1)

    v_norm = args.version.replace(".", "_").lower()
    
    # Check that no data files were created (parquet, csv, sqlite)
    for ext in ["*.parquet", "*.csv", "*.sqlite", "*.db", "*.jsonl"]:
        files = list(Path(".").rglob(ext))
        # Exclude things in .venv or node_modules or caches
        bad_files = [str(f) for f in files if ".venv" not in str(f) and "scratch" not in str(f) and "tests" not in str(f) and "reports/evaluation" not in str(f)]
        if bad_files:
            print(f"ERROR: Found forbidden data files: {bad_files}")
            sys.exit(1)

    # 1. Check all required JSON files are present
    required_reports = [
        f"microstructure_wrapper_plan_input_guard_{v_norm}.json",
        f"microstructure_wrapper_scope_definition_{v_norm}.json",
        f"microstructure_collector_interface_plan_{v_norm}.json",
        f"microstructure_network_interception_policy_{v_norm}.json",
        f"microstructure_write_interception_policy_{v_norm}.json",
        f"microstructure_request_mocking_policy_{v_norm}.json",
        f"microstructure_manifest_preview_policy_{v_norm}.json",
        f"microstructure_wrapper_test_plan_{v_norm}.json",
        f"microstructure_wrapper_decision_{v_norm}.json",
        f"microstructure_wrapper_recommendation_{v_norm}.json",
        f"microstructure_wrapper_plan_summary_{v_norm}.json",
        f"microstructure_wrapper_plan_consistency_check_{v_norm}.json",
        f"{v_norm}_recommendation.json",
    ]
    
    reports_data = {}
    for r in required_reports:
        p = Path("reports/research") / r
        if not p.exists():
            print(f"ERROR: Missing JSON report {r}")
            sys.exit(1)
        try:
            with open(p) as f:
                data = json.load(f)
                reports_data[r] = data
        except json.JSONDecodeError:
            print(f"ERROR: JSON report not parseable {r}")
            sys.exit(1)

    # 2. Check MD files are present
    for r in required_reports:
        p = Path("reports/research") / r.replace(".json", ".md")
        if not p.exists():
            print(f"ERROR: Missing MD report {p.name}")
            sys.exit(1)
            
    # Final doc
    final_doc = Path(f"docs/microstructure_network_disabled_wrapper_plan_{v_norm}.md")
    if not final_doc.exists():
        print(f"ERROR: Missing final doc {final_doc.name}")
        sys.exit(1)
        
    summary = reports_data[f"microstructure_wrapper_plan_summary_{v_norm}.json"]
    consistency = reports_data[f"microstructure_wrapper_plan_consistency_check_{v_norm}.json"]
    recommendation = reports_data[f"{v_norm}_recommendation.json"]
    
    # Load PROJECT_STATE and latest_metrics
    try:
        with open("reports/PROJECT_STATE.json") as f:
            project_state = json.load(f)
        with open("reports/current/latest_metrics.json") as f:
            latest_metrics = json.load(f)
    except FileNotFoundError:
        print("ERROR: Missing PROJECT_STATE or latest_metrics")
        sys.exit(1)

    # NaN / Infinity check
    def check_finite(obj: object) -> bool:
        if isinstance(obj, dict):
            return all(check_finite(v) for v in obj.values())
        if isinstance(obj, list):
            return all(check_finite(x) for x in obj)
        if isinstance(obj, float):
            return math.isfinite(obj)
        return True
        
    for r, data in reports_data.items():
        if not check_finite(data):
            print(f"ERROR: NaN/Infinity found in {r}")
            sys.exit(1)

    # Verification of summary vs PROJECT_STATE vs latest_metrics vs recommendation
    def verify_alignment(field: str):
        val_sum = summary.get(field)
        val_ps = project_state.get(field)
        val_lm = latest_metrics.get(field)
        val_rec = recommendation.get(field)
        if not (val_sum == val_ps == val_lm == val_rec):
            print(f"ERROR: Alignment mismatch for {field}: sum={val_sum}, ps={val_ps}, lm={val_lm}, rec={val_rec}")
            sys.exit(1)

    verify_alignment("final_verdict")
    verify_alignment("wrapper_plan_ready")
    verify_alignment("recommended_next_step")
    verify_alignment("next_allowed_phase")
    
    # 3. Version and alignment checks
    for state_name, state in [("summary", summary), ("recommendation", recommendation), ("project_state", project_state), ("latest_metrics", latest_metrics)]:
        if state.get("version") != "V1.63.2":
            print(f"ERROR: Invalid version in {state_name}: {state.get('version')}")
            sys.exit(1)
        if state.get("current_version") != "V1.63.2":
            print(f"ERROR: Invalid current_version in {state_name}: {state.get('current_version')}")
            sys.exit(1)
        if state.get("previous_version") != "V1.63.1":
            print(f"ERROR: Invalid previous_version in {state_name}: {state.get('previous_version')}")
            sys.exit(1)
        if state.get("previous_base") != "V1.63.1":
            print(f"ERROR: Invalid previous_base in {state_name}: {state.get('previous_base')}")
            sys.exit(1)
        if state.get("verdict_alignment_status") != "WRAPPER_PLAN_VERDICT_ALIGNED":
            print(f"ERROR: Invalid verdict_alignment_status in {state_name}")
            sys.exit(1)
            
        # Summary consistency check status present check
        if state.get("summary_consistency_check_status_present") is not True:
            print(f"ERROR: summary_consistency_check_status_present missing or False in {state_name}")
            sys.exit(1)

    # Summary specific checks
    if summary.get("consistency_check_status") != "MICROSTRUCTURE_WRAPPER_PLAN_REPORTS_CONSISTENT_INFRASTRUCTURE_ONLY":
        print("ERROR: summary missing or has incorrect consistency_check_status")
        sys.exit(1)
    if "status" in summary:
        print("ERROR: summary must not contain 'status' field")
        sys.exit(1)
    if summary.get("status_field_policy") != "REMOVED":
        print("ERROR: summary status_field_policy must be REMOVED")
        sys.exit(1)
    if summary.get("status_field_present") is not False:
        print("ERROR: summary status_field_present must be False")
        sys.exit(1)
        
    for state in [summary, project_state, latest_metrics]:
        assert state.get("state_alignment_status") == "WRAPPER_PLAN_STATE_ALIGNED"
        assert state.get("version_normalization_status") == "VERSION_NORMALIZED"
        assert state.get("stale_hardened_preflight_review_status_removed") is True

    # Hardcoded verifications for consistency check
    assert consistency.get("version") == args.version, "Consistency version mismatch"
    assert consistency.get("previous_base") == "V1.63.1", "Consistency previous_base mismatch"
    assert consistency.get("issues") == [], "Consistency issues not empty"
    assert consistency.get("consistency_check_status") == "MICROSTRUCTURE_WRAPPER_PLAN_REPORTS_CONSISTENT_INFRASTRUCTURE_ONLY"
    assert consistency.get("verdict_alignment_status") == "WRAPPER_PLAN_VERDICT_ALIGNED"
    assert consistency.get("project_state_verdict_aligned") is True
    assert consistency.get("latest_metrics_verdict_aligned") is True
    assert consistency.get("recommendation_verdict_aligned") is True
    assert consistency.get("required_reports_present") is True
    assert consistency.get("required_markdown_reports_present") is True
    assert consistency.get("project_state_aligned") is True
    assert consistency.get("latest_metrics_aligned") is True
    assert consistency.get("latest_summary_aligned") is True
    assert consistency.get("summary_consistency_check_status_present") is True
    assert consistency.get("status_field_policy") == "REMOVED"
    assert consistency.get("status_field_present") is False
    
    for state in [summary, project_state, latest_metrics, recommendation]:
        assert state.get("wrapper_plan_only") is True
        assert state.get("wrapper_executed") is False
        assert state.get("previous_hardened_preflight_review_passed") is True
        assert state.get("previous_final_verdict") == "MICROSTRUCTURE_HARDENED_PREFLIGHT_REVIEW_PASSED"
        assert state.get("controlled_local_preflight_executed") is False
        assert state.get("real_preflight_executed") is False
        assert state.get("network_enabled") is False
        assert state.get("network_disabled") is True
        assert state.get("network_disabled_by_default") is True
        assert state.get("future_network_activation_requires_separate_approval") is True
        assert state.get("real_collection_approved") is False
        assert state.get("real_collection_approval_status") == "NOT_APPROVED"
        assert state.get("real_collection_executed") is False
        assert state.get("human_review_required_before_collection") is True
        assert state.get("dry_run_only") is True
        assert state.get("local_fixture_only") is True
        assert state.get("fixture_only") is True
        assert state.get("synthetic_or_minimal_sample") is True
        assert state.get("not_for_research_results") is True
        assert state.get("simulated_requests_allowed") is True
        assert state.get("requests_executed_count") == 0
        assert state.get("external_api_called") is False
        assert state.get("external_data_downloaded") is False
        assert state.get("new_data_files_created") is False
        assert state.get("no_data_directory_writes") is True
        assert state.get("parquet_created") is False
        assert state.get("csv_created") is False
        assert state.get("sqlite_created") is False
        assert state.get("manifest_preview_policy_defined") is True
        assert state.get("manifest_data_file_created") is False
        assert state.get("network_interception_defined") is True
        assert state.get("write_interception_defined") is True
        assert state.get("request_mocking_defined") is True
        assert state.get("wrapper_tests_defined") is True
        assert state.get("no_new_filter") is True
        assert state.get("no_strategy_validated") is True
        assert state.get("no_preregistration_yet") is True
        assert state.get("no_paper_live") is True
        assert state.get("no_real_trading") is True
        assert state.get("holdout_executed") is False
        assert state.get("codex_cli_called") is False
        assert state.get("real_orders_possible") is False

        fv = state.get("final_verdict")
        assert "VALIDATED" not in fv
        assert "REAL_COLLECTION_APPROVED" not in fv
        assert "NETWORK_ENABLED" not in fv
        assert "WRAPPER_EXECUTED" not in fv

        rec_step = state.get("recommended_next_step", "")
        for forbidden in ["real collection", "live collection", "paper live", "real trading", "preregistration", "enable network now"]:
            assert forbidden not in rec_step

        if state.get("wrapper_plan_ready"):
            assert state.get("next_allowed_phase") == "network_disabled_wrapper_fixture_implementation"
            assert "implement network-disabled wrapper with local fixtures only" in rec_step
        else:
            assert state.get("next_allowed_phase") == "more_wrapper_planning"
            assert "refine network-disabled wrapper plan" in rec_step

    # Check for 'status' field in any reports if policy is REMOVED
    for r, data in reports_data.items():
        if "status" in data:
            print(f"ERROR: Report {r} contains forbidden 'status' field")
            sys.exit(1)

    print("SUCCESS: Wrapper plan validation passed.")


if __name__ == "__main__":
    main()
