import json
import argparse
from pathlib import Path

def validate_reports(version: str):
    # Strict version casing check
    if version.startswith("v1."):
        raise ValueError(f"Version must start with uppercase V, got: {version}")
    if "_" in version:
        raise ValueError(f"Version must use dot separator, got: {version}")

    v_norm = version.lower().replace(".", "_")
    reports_dir = Path("reports/research")
    
    required_stems = [
        "microstructure_preflight_plan_input_guard",
        "microstructure_preflight_scope_definition",
        "microstructure_preflight_network_gate_policy",
        "microstructure_preflight_write_gate_policy",
        "microstructure_preflight_request_execution_policy",
        "microstructure_preflight_manifest_expectation_plan",
        "microstructure_preflight_rollback_cleanup_policy",
        "microstructure_preflight_stop_condition_policy",
        "microstructure_preflight_dryrun_test_plan",
        "microstructure_preflight_decision",
        "microstructure_preflight_recommendation",
        "microstructure_preflight_plan_summary",
        "microstructure_preflight_plan_consistency_check",
        f"v1_59_1_recommendation"
    ]
    
    for stem in required_stems:
        # Avoid double suffix if stem already includes version
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
            
        # Parse JSON
        with open(json_path, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in {json_path}: {e}")
            
        # Check finiteness (no NaN/Inf)
        json_str = json.dumps(data)
        if "NaN" in json_str or "Infinity" in json_str:
            raise ValueError(f"JSON contains non-finite values: {json_path}")

        # Check version in summary, consistency_check, recommendation
        if any(x in stem for x in ["summary", "consistency_check", "recommendation"]):
            if data.get("version") != version:
                raise ValueError(f"Version mismatch in {json_path}: expected {version}, got {data.get('version')}")
            if data.get("current_version") != version:
                raise ValueError(f"current_version mismatch in {json_path}: expected {version}, got {data.get('current_version')}")

    # Specific check on recommendation
    rec_path = reports_dir / f"v1_59_1_recommendation.json"
    with open(rec_path, "r") as f:
        rec = json.load(f)
    
    mandatory_safety_fields = [
        "real_collection_approved",
        "real_collection_approval_status",
        "human_review_required_before_collection",
        "network_disabled",
        "preflight_executed",
        "preflight_plan_only",
        "external_api_called",
        "external_data_downloaded",
        "requests_executed_count",
        "no_strategy_validated",
        "no_paper_live",
        "no_real_trading",
        "holdout_executed",
        "codex_cli_called",
        "real_orders_possible",
        "dry_run_only",
        "local_fixture_only",
        "fixture_only",
        "synthetic_or_minimal_sample",
        "not_for_research_results",
        "safety_flags_alignment_status",
        "safety_flags_complete"
    ]
    
    for field in mandatory_safety_fields:
        if field not in rec:
            raise ValueError(f"Missing mandatory safety field in recommendation: {field}")

    if rec.get("real_collection_approved") is not False:
        raise ValueError("real_collection_approved must be False")
    if rec.get("real_collection_approval_status") != "NOT_APPROVED":
        raise ValueError("real_collection_approval_status must be NOT_APPROVED")
    if rec.get("network_disabled") is not True:
        raise ValueError("network_disabled must be True")
    if rec.get("preflight_executed") is not False:
        raise ValueError("preflight_executed must be False")
    if rec.get("preflight_plan_only") is not True:
        raise ValueError("preflight_plan_only must be True")
    if rec.get("requests_executed_count") != 0:
        raise ValueError("requests_executed_count must be 0")
    if rec.get("no_strategy_validated") is not True:
        raise ValueError("no_strategy_validated must be True")
    if rec.get("no_real_trading") is not True:
        raise ValueError("no_real_trading must be True")
    if rec.get("no_paper_live") is not True:
        raise ValueError("no_paper_live must be True")
    if rec.get("dry_run_only") is not True:
        raise ValueError("dry_run_only must be True")
    if rec.get("local_fixture_only") is not True:
        raise ValueError("local_fixture_only must be True")
    if rec.get("fixture_only") is not True:
        raise ValueError("fixture_only must be True")
    if rec.get("synthetic_or_minimal_sample") is not True:
        raise ValueError("synthetic_or_minimal_sample must be True")
    if rec.get("not_for_research_results") is not True:
        raise ValueError("not_for_research_results must be True")
    if rec.get("safety_flags_alignment_status") != "SAFETY_FLAGS_ALIGNED":
        raise ValueError("safety_flags_alignment_status must be SAFETY_FLAGS_ALIGNED")
    if rec.get("safety_flags_complete") is not True:
        raise ValueError("safety_flags_complete must be True")

        
    # Check recommended_next_step for forbidden keywords
    forbidden_keywords = ["real collection", "live collection", "paper live", "real trading", "preregistration", "enable network now"]
    next_step = rec.get("recommended_next_step", "").lower()
    for kw in forbidden_keywords:
        if kw in next_step:
            raise ValueError(f"Forbidden keyword '{kw}' found in recommended_next_step")

    # Check final_verdict
    verdict = rec.get("final_verdict", "")
    if any(x in verdict for x in ["VALIDATED", "REAL_COLLECTION_APPROVED", "NETWORK_ENABLED"]):
        raise ValueError(f"Forbidden verdict: {verdict}")

    # Check consistency check
    consistency_path = reports_dir / f"microstructure_preflight_plan_consistency_check_{v_norm}.json"
    with open(consistency_path, "r") as f:
        cc = json.load(f)
    
    if cc.get("issues") != []:
        raise ValueError(f"Consistency check contains issues: {cc.get('issues')}")
    
    mandatory_cc_flags = [
        "preflight_plan_ready",
        "preflight_plan_only",
        "preflight_executed",
        "network_enabled",
        "network_disabled",
        "network_disabled_by_default",
        "future_network_activation_requires_separate_approval",
        "real_collection_approved",
        "real_collection_executed",
        "manifest_expectations_defined",
        "stop_conditions_defined",
        "rollback_policy_defined",
        "dryrun_tests_defined",
        "dry_run_only",
        "local_fixture_only",
        "fixture_only",
        "synthetic_or_minimal_sample",
        "not_for_research_results",
        "safety_flags_alignment_status",
        "safety_flags_complete"
    ]
    for flag in mandatory_cc_flags:
        if flag not in cc:
             raise ValueError(f"Missing mandatory flag in consistency check: {flag}")

    if cc.get("network_enabled") is not False:
        raise ValueError("network_enabled must be False in consistency check")
    if cc.get("preflight_executed") is not False:
        raise ValueError("preflight_executed must be False in consistency check")
    if cc.get("preflight_plan_only") is not True:
        raise ValueError("preflight_plan_only must be True in consistency check")
    if cc.get("dry_run_only") is not True:
        raise ValueError("dry_run_only must be True in consistency check")
    if cc.get("local_fixture_only") is not True:
        raise ValueError("local_fixture_only must be True in consistency check")
    if cc.get("safety_flags_alignment_status") != "SAFETY_FLAGS_ALIGNED":
        raise ValueError("safety_flags_alignment_status must be SAFETY_FLAGS_ALIGNED in consistency check")


    # Check PROJECT_STATE and latest_metrics
    for p in [Path("reports/PROJECT_STATE.json"), Path("reports/current/latest_metrics.json")]:
        if p.exists():
            with open(p, "r") as f:
                state_data = json.load(f)
            if state_data.get("version") != version:
                raise ValueError(f"Version mismatch in {p}: expected {version}, got {state_data.get('version')}")
            if state_data.get("network_enabled") is not False:
                raise ValueError(f"network_enabled must be False in {p}")
            if state_data.get("preflight_executed") is not False:
                raise ValueError(f"preflight_executed must be False in {p}")
            if state_data.get("dry_run_only") is not True:
                raise ValueError(f"dry_run_only must be True in {p}")
            if state_data.get("local_fixture_only") is not True:
                raise ValueError(f"local_fixture_only must be True in {p}")
            if state_data.get("fixture_only") is not True:
                raise ValueError(f"fixture_only must be True in {p}")
            if state_data.get("safety_flags_alignment_status") != "SAFETY_FLAGS_ALIGNED":
                raise ValueError(f"safety_flags_alignment_status must be SAFETY_FLAGS_ALIGNED in {p}")
            if state_data.get("consistency_check_status") not in [
                "MICROSTRUCTURE_PREFLIGHT_PLAN_REPORTS_CONSISTENT_INFRASTRUCTURE_ONLY"
            ]:
                raise ValueError(f"Invalid consistency_check_status in {p}")


    # Check for forbidden files in data/
    forbidden_exts = [".parquet", ".csv", ".sqlite", ".db", ".jsonl"]
    if Path("data").exists():
        for p in Path("data").rglob("*"):
            if p.suffix in forbidden_exts:
                raise ValueError(f"Forbidden data file found: {p}")

    # Check final doc
    final_doc = Path(f"docs/microstructure_controlled_preflight_plan_{v_norm}.md")
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
