import argparse
import json
import math
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    # V1.64.2 Specific Hardening
    if args.version.lower() not in ["v1.64", "v1.64.1", "v1.64.2"]:
        print(f"ERROR: Validator expects V1.64, V1.64.1 or V1.64.2, got {args.version}")
        sys.exit(1)

    v_norm = args.version.replace(".", "_").lower()
    
    # Check that no data files were created (parquet, csv, sqlite)
    for ext in ["*.parquet", "*.csv", "*.sqlite", "*.db", "*.jsonl"]:
        files = list(Path(".").rglob(ext))
        bad_files = [str(f) for f in files if ".venv" not in str(f) and "scratch" not in str(f) and "tests" not in str(f) and "reports/evaluation" not in str(f)]
        if bad_files:
            print(f"ERROR: Found forbidden data files: {bad_files}")
            sys.exit(1)

    # 1. Check all required JSON files are present
    required_reports = [
        f"microstructure_wrapper_fixture_input_guard_{v_norm}.json",
        f"microstructure_network_disabled_wrapper_{v_norm}.json",
        f"microstructure_network_gate_{v_norm}.json",
        f"microstructure_write_gate_{v_norm}.json",
        f"microstructure_fixture_request_loader_{v_norm}.json",
        f"microstructure_fixture_response_adapter_{v_norm}.json",
        f"microstructure_manifest_preview_builder_{v_norm}.json",
        f"microstructure_wrapper_fixture_runner_{v_norm}.json",
        f"microstructure_wrapper_safety_audit_{v_norm}.json",
        f"microstructure_wrapper_fixture_decision_{v_norm}.json",
        f"microstructure_wrapper_fixture_recommendation_{v_norm}.json",
        f"microstructure_wrapper_fixture_summary_{v_norm}.json",
        f"microstructure_wrapper_fixture_consistency_check_{v_norm}.json",
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
                # Check for NaN / Infinity
                content = json.dumps(data)
                if "NaN" in content or "Infinity" in content:
                    print(f"ERROR: JSON report contains NaN or Infinity: {r}")
                    sys.exit(1)
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
    final_doc = Path(f"docs/microstructure_network_disabled_wrapper_fixture_{v_norm}.md")
    if not final_doc.exists():
        print(f"ERROR: Missing final doc {final_doc.name}")
        sys.exit(1)
        
    summary = reports_data[f"microstructure_wrapper_fixture_summary_{v_norm}.json"]
    consistency = reports_data[f"microstructure_wrapper_fixture_consistency_check_{v_norm}.json"]
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
    verify_alignment("wrapper_fixture_implementation_passed")
    verify_alignment("recommended_next_step")
    verify_alignment("next_allowed_phase")
    
    # 3. Version and alignment checks
    for state_name, state in [("summary", summary), ("recommendation", recommendation), ("project_state", project_state), ("latest_metrics", latest_metrics)]:
        if state.get("version").upper() != args.version.upper():
            print(f"ERROR: Invalid version in {state_name}: {state.get('version')}")
            sys.exit(1)
        if state.get("verdict_alignment_status") != "WRAPPER_FIXTURE_VERDICT_ALIGNED":
            print(f"ERROR: Invalid verdict_alignment_status in {state_name}")
            sys.exit(1)

        # Reporting completeness checks for V1.64.1/V1.64.2
        if args.version.lower() in ["v1.64.1", "v1.64.2"]:
            required_fields = [
                "consistency_check_status",
                "project_state_verdict_aligned",
                "latest_metrics_verdict_aligned",
                "recommendation_verdict_aligned",
                "new_data_files_created",
                "jsonl_created",
                "db_created",
                "manifest_preview_generated",
                "normalized_records_preview_generated",
                "network_interception_defined",
                "write_interception_defined",
                "request_mocking_defined",
                "wrapper_tests_defined",
                "reporting_completeness_status",
                "summary_required_fields_complete",
                "recommendation_required_fields_complete",
                "project_state_required_fields_complete",
                "latest_metrics_required_fields_complete",
                "previous_wrapper_plan_ready",
                "previous_final_verdict"
            ]
            for f in required_fields:
                if f not in state:
                    print(f"ERROR: Missing required field {f} in {state_name}")
                    sys.exit(1)
            
            if state.get("reporting_completeness_status") != "WRAPPER_FIXTURE_REPORTING_COMPLETE":
                print(f"ERROR: Invalid reporting_completeness_status in {state_name}")
                sys.exit(1)
            if not all([state.get("summary_required_fields_complete"), state.get("recommendation_required_fields_complete"), state.get("project_state_required_fields_complete"), state.get("latest_metrics_required_fields_complete")]):
                print(f"ERROR: Completeness flags false in {state_name}")
                sys.exit(1)
            if state.get("previous_final_verdict") != "MICROSTRUCTURE_NETWORK_DISABLED_WRAPPER_PLAN_READY":
                print(f"ERROR: Invalid previous_final_verdict in {state_name}: {state.get('previous_final_verdict')}")
                sys.exit(1)
            if state.get("previous_wrapper_plan_ready") is not True:
                print(f"ERROR: previous_wrapper_plan_ready not true in {state_name}")
                sys.exit(1)

            if state_name in ["summary", "recommendation", "project_state", "latest_metrics"]:
                data_flags = ["parquet_created", "csv_created", "sqlite_created", "manifest_data_file_created"]
                for f in data_flags:
                    if f not in state:
                        print(f"ERROR: Missing data flag {f} in {state_name}")
                        sys.exit(1)
                    if state.get(f) is not False:
                        print(f"ERROR: Data flag {f} must be false in {state_name}")
                        sys.exit(1)

            if state_name == "recommendation":
                extra_rec_fields = [
                    "status_field_policy",
                    "status_field_present",
                    "no_paper_live",
                    "no_preregistration_yet",
                    "holdout_executed",
                    "codex_cli_called",
                    "real_orders_possible",
                    "wrapper_fixture_only",
                    "wrapper_plan_only",
                    "wrapper_fixture_run_executed",
                    "wrapper_real_execution",
                    "wrapper_executed",
                    "network_gate_enabled",
                    "write_gate_enabled",
                    "network_disabled",
                    "requests_executed_count",
                    "external_api_called",
                    "external_data_downloaded",
                    "no_data_directory_writes"
                ]
                for f in extra_rec_fields:
                    if f not in state:
                        print(f"ERROR: Missing required field {f} in recommendation")
                        sys.exit(1)

    # 4. Consistency status check
    if args.version.lower() in ["v1.64.1", "v1.64.2"]:
        if consistency.get("reporting_completeness_status") != "WRAPPER_FIXTURE_REPORTING_COMPLETE":
            print("ERROR: reporting_completeness_status mismatch in consistency check")
            sys.exit(1)
        if not all([
            consistency.get("summary_required_fields_complete"),
            consistency.get("recommendation_required_fields_complete"),
            consistency.get("project_state_required_fields_complete"),
            consistency.get("latest_metrics_required_fields_complete"),
            consistency.get("project_state_verdict_aligned"),
            consistency.get("latest_metrics_verdict_aligned"),
            consistency.get("recommendation_verdict_aligned"),
            consistency.get("previous_wrapper_plan_ready"),
        ]):
            print("ERROR: Required fields completeness flags false in consistency check")
            sys.exit(1)
        if consistency.get("previous_final_verdict") != "MICROSTRUCTURE_NETWORK_DISABLED_WRAPPER_PLAN_READY":
            print("ERROR: Invalid previous_final_verdict in consistency check")
            sys.exit(1)
            
    # Hardcoded verifications for summary
    assert summary.get("wrapper_fixture_only") is True
    assert summary.get("wrapper_plan_only") is False
    assert summary.get("wrapper_real_execution") is False
    assert summary.get("wrapper_executed") is False
    assert summary.get("network_gate_enabled") is True
    assert summary.get("write_gate_enabled") is True
    assert summary.get("network_enabled") is False
    assert summary.get("network_disabled") is True
    assert summary.get("requests_executed_count") == 0
    assert summary.get("no_data_directory_writes") is True
    
    # Hardcoded verifications for consistency check
    assert consistency.get("version").upper() == args.version.upper()
    assert consistency.get("issues") == []
    assert consistency.get("consistency_check_status") == "MICROSTRUCTURE_WRAPPER_FIXTURE_REPORTS_CONSISTENT_INFRASTRUCTURE_ONLY"
    
    for state in [summary, project_state, latest_metrics, recommendation]:
        assert state.get("real_collection_approved") is False
        assert state.get("real_collection_executed") is False
        assert state.get("network_enabled") is False
        assert state.get("no_new_filter") is True
        assert state.get("no_strategy_validated") is True
        assert state.get("no_real_trading") is True
        
        fv = state.get("final_verdict")
        assert "VALIDATED" not in fv
        assert "REAL_COLLECTION_APPROVED" not in fv
        assert "NETWORK_ENABLED" not in fv
        assert "REAL_WRAPPER_EXECUTED" not in fv

        if state.get("wrapper_fixture_implementation_passed"):
            assert state.get("next_allowed_phase") == "network_disabled_wrapper_fixture_execution_review"
            assert "review network-disabled wrapper fixture execution" in state.get("recommended_next_step")
        else:
            assert state.get("next_allowed_phase") == "more_wrapper_fixture_implementation"
            assert "continue implementing network-disabled wrapper" in state.get("recommended_next_step")

    print(f"SUCCESS: Wrapper fixture implementation validation passed for {args.version}.")



if __name__ == "__main__":
    main()
