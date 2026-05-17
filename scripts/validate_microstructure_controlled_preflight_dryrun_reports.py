import json
import argparse
from pathlib import Path

def validate_reports(version: str):
    if version != "V1.60.2" and version != "v1.60.2":
         # Standardize version
         version = "V1.60.2"

    v_norm = version.lower().replace(".", "_")
    reports_dir = Path("reports/research")
    
    required_stems = [
        "microstructure_preflight_dryrun_input_guard",
        "microstructure_local_fixture_preflight_run",
        "microstructure_network_block_verification",
        "microstructure_write_block_verification",
        "microstructure_request_simulation_verification",
        "microstructure_manifest_dryrun_validation",
        "microstructure_timestamp_causality_validation",
        "microstructure_stop_condition_simulation",
        "microstructure_cleanup_verification",
        "microstructure_preflight_dryrun_decision",
        "microstructure_preflight_dryrun_recommendation",
        "microstructure_preflight_dryrun_summary",
        "microstructure_preflight_dryrun_consistency_check",
        "v1_60_2_recommendation"
    ]
    
    for stem in required_stems:
        if v_norm in stem:
            filename_json = f"{stem}.json"
            filename_md = f"{stem}.md"
        else:
            filename_json = f"{stem}_{v_norm}.json"
            filename_md = f"{stem}_{v_norm}.md"
            
        json_path = reports_dir / filename_json
        md_path = reports_dir / filename_md
        
        if not json_path.exists():
            raise FileNotFoundError(f"Missing mandatory JSON report: {json_path}")
        if not md_path.exists():
            raise FileNotFoundError(f"Missing mandatory MD report: {md_path}")
            
        with open(json_path, "r") as f:
            data = json.load(f)
            
        json_str = json.dumps(data)
        if "NaN" in json_str or "Infinity" in json_str:
            raise ValueError(f"JSON contains non-finite values: {json_path}")

    # Load summary for comparison
    summary_path = reports_dir / f"microstructure_preflight_dryrun_summary_{v_norm}.json"
    with open(summary_path, "r") as f:
        summary = json.load(f)
    
    # Check consistency check
    cc_path = reports_dir / f"microstructure_preflight_dryrun_consistency_check_{v_norm}.json"
    with open(cc_path, "r") as f:
        cc = json.load(f)

    # Check recommendation
    rec_path = reports_dir / f"v1_60_2_recommendation.json"
    with open(rec_path, "r") as f:
        rec = json.load(f)

    # Check PROJECT_STATE and latest_metrics
    state_path = Path("reports/PROJECT_STATE.json")
    metrics_path = Path("reports/current/latest_metrics.json")
    
    with open(state_path, "r") as f:
        state = json.load(f)
    with open(metrics_path, "r") as f:
        metrics = json.load(f)

    # VERDICT ALIGNMENT HARDENING
    for doc in [summary, cc, rec, state, metrics]:
        doc_name = "doc"
        if doc == summary: doc_name = "summary"
        if doc == cc: doc_name = "consistency_check"
        if doc == rec: doc_name = "recommendation"
        if doc == state: doc_name = "PROJECT_STATE"
        if doc == metrics: doc_name = "latest_metrics"

        if doc.get("final_verdict") != summary.get("final_verdict"):
            raise ValueError(f"Verdict mismatch in {doc_name}: expected {summary.get('final_verdict')}, got {doc.get('final_verdict')}")
        if doc.get("preflight_dryrun_passed") != summary.get("preflight_dryrun_passed"):
            raise ValueError(f"preflight_dryrun_passed mismatch in {doc_name}")
        if doc.get("recommended_next_step") != summary.get("recommended_next_step"):
            raise ValueError(f"recommended_next_step mismatch in {doc_name}")
        if doc.get("next_allowed_phase") != summary.get("next_allowed_phase"):
            raise ValueError(f"next_allowed_phase mismatch in {doc_name}")

    # Logical constraints
    if summary.get("preflight_dryrun_passed") is False:
        if "PASSED" in summary.get("final_verdict"):
            raise ValueError("preflight_dryrun_passed=false but final_verdict contains PASSED")
        if summary.get("next_allowed_phase") != "more_preflight_hardening":
            raise ValueError("preflight_dryrun_passed=false but next_allowed_phase is not more_preflight_hardening")
        if "review results" in summary.get("recommended_next_step"):
            raise ValueError("preflight_dryrun_passed=false but recommended_next_step suggests review")
    else:
        if "FAILED" in summary.get("final_verdict"):
            raise ValueError("preflight_dryrun_passed=true but final_verdict contains FAILED")
        if summary.get("next_allowed_phase") != "controlled_preflight_review":
            raise ValueError("preflight_dryrun_passed=true but next_allowed_phase is not controlled_preflight_review")
        if "harden" in summary.get("recommended_next_step"):
            raise ValueError("preflight_dryrun_passed=true but recommended_next_step suggests hardening")

    # Alignment status
    if summary.get("verdict_alignment_status") != "PREFLIGHT_DRYRUN_VERDICT_ALIGNED":
        raise ValueError("Missing or invalid verdict_alignment_status")
    if cc.get("project_state_verdict_aligned") is not True:
        raise ValueError("project_state_verdict_aligned must be True")
    if cc.get("latest_metrics_verdict_aligned") is not True:
        raise ValueError("latest_metrics_verdict_aligned must be True")
    if cc.get("recommendation_verdict_aligned") is not True:
        raise ValueError("recommendation_verdict_aligned must be True")

    # Safety flags
    mandatory_safety_fields = [
        "controlled_local_preflight_executed",
        "preflight_execution_mode",
        "real_preflight_executed",
        "network_enabled",
        "network_disabled",
        "real_collection_approved",
        "real_collection_approval_status",
        "human_review_required_before_collection",
        "dry_run_only",
        "local_fixture_only",
        "fixture_only",
        "external_api_called",
        "external_data_downloaded",
        "requests_executed_count",
        "no_strategy_validated",
        "no_paper_live",
        "no_real_trading",
        "holdout_executed",
        "codex_cli_called",
        "real_orders_possible",
        "preflight_dryrun_passed",
        "preflight_plan_only",
        "next_allowed_phase",
        "network_disabled_by_default",
        "real_collection_executed",
        "simulated_requests_count",
        "new_data_files_created",
        "no_data_directory_writes",
        "parquet_created",
        "csv_created",
        "sqlite_created",
        "manifest_preview_generated",
        "manifest_data_file_created",
        "timestamp_causality_passed",
        "no_lookahead_confirmed",
        "stop_conditions_simulated",
        "cleanup_verified",
        "no_new_filter",
        "no_preregistration_yet",
        "reporting_alignment_status",
        "recommendation_safety_fields_complete"
    ]
    
    for field in mandatory_safety_fields:
        if field not in rec:
            raise ValueError(f"Missing mandatory safety field in recommendation: {field}")

    # General state checks
    if state.get("version") != "V1.60.2":
        raise ValueError(f"Version mismatch in PROJECT_STATE.json: expected V1.60.2, got {state.get('version')}")
    if state.get("network_enabled") is not False:
        raise ValueError("network_enabled must be False")
    if state.get("real_collection_approved") is not False:
        raise ValueError("real_collection_approved must be False")
    if state.get("requests_executed_count") != 0:
        raise ValueError("requests_executed_count must be 0")

    # Forbidden strings in recommended_next_step
    forbidden_words = ["real collection", "live collection", "paper live", "real trading", "preregistration", "enable network now"]
    for word in forbidden_words:
        if word in summary.get("recommended_next_step").lower():
            raise ValueError(f"Forbidden word in recommended_next_step: {word}")

    # Forbidden verdicts
    forbidden_verdicts = ["VALIDATED", "REAL_COLLECTION_APPROVED", "NETWORK_ENABLED"]
    for v in forbidden_verdicts:
        if v in summary.get("final_verdict"):
            raise ValueError(f"Forbidden verdict: {v}")

    # Data check
    forbidden_exts = [".parquet", ".csv", ".sqlite", ".db", ".jsonl"]
    if Path("data").exists():
        for p in Path("data").rglob("*"):
            if p.is_file() and p.suffix in forbidden_exts:
                raise ValueError(f"Forbidden data file found: {p}")

    # Doc check
    final_doc = Path(f"docs/microstructure_controlled_preflight_dryrun_{v_norm}.md")
    if not final_doc.exists():
        raise FileNotFoundError(f"Missing final documentation: {final_doc}")

    print(f"Validation for {version} PASSED.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    try:
        validate_reports(args.version)
    except Exception as e:
        print(f"VALIDATION FAILED: {e}")
        exit(1)
