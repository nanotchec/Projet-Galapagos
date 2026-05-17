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
        "microstructure_offline_review_input_guard",
        "microstructure_offline_review_checklist",
        "microstructure_human_review_items",
        "microstructure_contract_risk_register",
        "microstructure_optional_field_review",
        "microstructure_offline_review_decision",
        "microstructure_preflight_boundary_policy",
        "microstructure_offline_review_safety_audit",
        "microstructure_offline_review_recommendation",
        "microstructure_offline_review_summary",
        "microstructure_offline_review_consistency_check",
        f"{v_norm}_recommendation"
    ]
    
    # Check for non-canonical versions in all JSON files in reports
    for p in Path("reports").rglob("*.json"):
        with open(p, "r") as f:
            try:
                data = json.load(f)
                if isinstance(data, dict):
                    v_field = data.get("version")
                    if isinstance(v_field, str):
                        if v_field in ["v1_58_2", "v1.58_2", "V1_58_2", "v1.58.2"]:
                            raise ValueError(f"Non-canonical version '{v_field}' found in {p}")
            except json.JSONDecodeError:
                pass

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
    rec_path = reports_dir / f"{v_norm}_recommendation.json"
    with open(rec_path, "r") as f:
        rec = json.load(f)
    
    mandatory_safety_fields = [
        "real_collection_approved",
        "real_collection_approval_status",
        "human_review_required_before_collection",
        "network_disabled",
        "dry_run_only",
        "local_fixture_only",
        "fixture_only",
        "synthetic_or_minimal_sample",
        "not_for_research_results",
        "real_collection_executed",
        "external_data_downloaded",
        "external_api_called",
        "new_data_files_created",
        "no_data_directory_writes",
        "parquet_created",
        "csv_created",
        "sqlite_created",
        "requests_executed_count",
        "no_new_filter",
        "no_strategy_validated",
        "no_preregistration_yet",
        "no_paper_live",
        "no_real_trading",
        "holdout_executed",
        "codex_cli_called",
        "real_orders_possible"
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
    if rec.get("requests_executed_count") != 0:
        raise ValueError("requests_executed_count must be 0")
    if rec.get("no_strategy_validated") is not True:
        raise ValueError("no_strategy_validated must be True")
    if rec.get("no_real_trading") is not True:
        raise ValueError("no_real_trading must be True")
    if rec.get("no_paper_live") is not True:
        raise ValueError("no_paper_live must be True")
        
    # Check recommended_next_step for forbidden keywords
    forbidden_keywords = ["real collection", "live collection", "paper live", "real trading", "preregistration"]
    next_step = rec.get("recommended_next_step", "").lower()
    for kw in forbidden_keywords:
        if kw in next_step:
            raise ValueError(f"Forbidden keyword '{kw}' found in recommended_next_step")

    # Check final_verdict
    verdict = rec.get("final_verdict", "")
    if "VALIDATED" in verdict or "REAL_COLLECTION_APPROVED" in verdict:
        raise ValueError(f"Forbidden verdict: {verdict}")

    # Check consistency check
    consistency_path = reports_dir / f"microstructure_offline_review_consistency_check_{v_norm}.json"
    with open(consistency_path, "r") as f:
        cc = json.load(f)
    
    if cc.get("issues") != []:
        raise ValueError(f"Consistency check contains issues: {cc.get('issues')}")
    if cc.get("recommendation_safety_fields_status") != "RECOMMENDATION_SAFETY_FIELDS_COMPLETE":
        raise ValueError("recommendation_safety_fields_status must be RECOMMENDATION_SAFETY_FIELDS_COMPLETE")
    if cc.get("version_normalization_status") != "VERSION_NORMALIZED":
        raise ValueError("version_normalization_status must be VERSION_NORMALIZED")
    if cc.get("release_audit_version_normalization_status") != "RELEASE_AUDIT_VERSION_NORMALIZED":
        raise ValueError("release_audit_version_normalization_status must be RELEASE_AUDIT_VERSION_NORMALIZED")
    if cc.get("release_audit_version_normalized") is not True:
        raise ValueError("release_audit_version_normalized must be True")

    # Check PROJECT_STATE and latest_metrics
    for p in [Path("reports/PROJECT_STATE.json"), Path("reports/current/latest_metrics.json")]:
        if p.exists():
            with open(p, "r") as f:
                state_data = json.load(f)
            if state_data.get("version") != version:
                raise ValueError(f"Version mismatch in {p}: expected {version}, got {state_data.get('version')}")
            if state_data.get("real_collection_approved") is not False:
                raise ValueError(f"real_collection_approved must be False in {p}")

    # Check Release Reports if they exist
    release_reports = [
        Path(f"reports/release_zip_{v_norm}.json"),
        Path(f"reports/zip_audit_{v_norm}.json"),
        Path(f"reports/zip_smoke_test_{v_norm}.json")
    ]
    for p in release_reports:
        if p.exists():
            with open(p, "r") as f:
                data = json.load(f)
            if data.get("version") != version:
                raise ValueError(f"Version mismatch in release report {p}: expected {version}, got {data.get('version')}")

    # Check for forbidden files in data/
    forbidden_exts = [".parquet", ".csv", ".sqlite", ".db", ".jsonl"]
    if Path("data").exists():
        for p in Path("data").rglob("*"):
            if p.suffix in forbidden_exts:
                raise ValueError(f"Forbidden data file found: {p}")

    # Check final doc
    final_doc = Path(f"docs/microstructure_collector_offline_review_{v_norm}.md")
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
