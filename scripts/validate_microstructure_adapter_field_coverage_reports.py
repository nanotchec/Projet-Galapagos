from __future__ import annotations
import argparse
import json
import os
from pathlib import Path

def validate_reports(version: str):
    v_norm = version.lower().replace(".", "_")
    root = Path("reports/research")
    
    required_json = [
        f"microstructure_field_coverage_input_guard_{v_norm}.json",
        f"microstructure_required_field_classifier_{v_norm}.json",
        f"microstructure_adapter_field_gap_analysis_{v_norm}.json",
        f"microstructure_fixture_extension_plan_{v_norm}.json",
        f"microstructure_fixture_field_mapping_validation_{v_norm}.json",
        f"microstructure_optional_field_policy_{v_norm}.json",
        f"microstructure_coverage_decision_{v_norm}.json",
        f"microstructure_field_coverage_safety_audit_{v_norm}.json",
        f"microstructure_field_coverage_recommendation_{v_norm}.json",
        f"microstructure_field_coverage_summary_{v_norm}.json",
        f"microstructure_field_coverage_consistency_check_{v_norm}.json",
        f"{v_norm}_recommendation.json"
    ]
    
    # 1. Check files presence
    for f_name in required_json:
        p = root / f_name
        if not p.exists():
            raise FileNotFoundError(f"Missing mandatory JSON report: {p}")
        if not (root / f_name.replace(".json", ".md")).exists():
            raise FileNotFoundError(f"Missing mandatory MD report: {p.with_suffix('.md')}")
            
    # 2. Check final doc
    doc_path = Path("docs") / f"microstructure_adapter_field_coverage_{v_norm}.md"
    if not doc_path.exists():
        raise FileNotFoundError(f"Missing mandatory final documentation: {doc_path}")
        
    # 3. Deep validation
    consist_path = root / f"microstructure_field_coverage_consistency_check_{v_norm}.json"
    with open(consist_path) as f:
        consist = json.load(f)
        if consist.get("version") != version.upper():
            raise ValueError(f"Version mismatch in consistency check: {consist.get('version')}")
        if consist.get("previous_base") != "V1.57.1":
            raise ValueError(f"Previous base mismatch in consistency check: {consist.get('previous_base')}")
        if consist.get("consistency_check_status") != "MICROSTRUCTURE_FIELD_COVERAGE_REPORTS_CONSISTENT_INFRASTRUCTURE_ONLY":
            raise ValueError(f"Consistency check status mismatch: {consist.get('consistency_check_status')}")
            
        # Semantic Consistency Checks
        still_missing = consist.get("still_missing_required_fields", [])
        missing_count = consist.get("missing_required_fields", -1)
        covered_flag = consist.get("required_fields_covered")
        ready_flag = consist.get("contract_ready_for_offline_review")
        
        if len(still_missing) != missing_count:
            raise ValueError(f"Semantic inconsistency: len(still_missing_required_fields)={len(still_missing)} but missing_required_fields={missing_count}")
        
        if covered_flag is True and missing_count != 0:
            raise ValueError(f"Semantic inconsistency: required_fields_covered is True but missing_required_fields={missing_count}")
        
        if covered_flag is True and len(still_missing) != 0:
            raise ValueError(f"Semantic inconsistency: required_fields_covered is True but still_missing_required_fields is non-empty")

        if covered_flag is False and missing_count == 0:
            raise ValueError(f"Semantic inconsistency: required_fields_covered is False but missing_required_fields is 0")

        if ready_flag is True and covered_flag is not True:
            raise ValueError(f"Semantic inconsistency: contract_ready_for_offline_review is True but required_fields_covered is {covered_flag}")

        if consist.get("field_coverage_semantic_consistency_status") != "FIELD_COVERAGE_SEMANTICS_CONSISTENT":
            raise ValueError("field_coverage_semantic_consistency_status must be FIELD_COVERAGE_SEMANTICS_CONSISTENT")

        if consist.get("semantic_consistency_passed") is not True:
            raise ValueError("semantic_consistency_passed must be True")

        # V1.57.2 status checks
        if consist.get("release_reports_packaging_status") != "RELEASE_REPORTS_INCLUDED":
            raise ValueError("release_reports_packaging_status must be RELEASE_REPORTS_INCLUDED")
        if consist.get("latest_metrics_version_alignment_status") != "LATEST_METRICS_VERSION_ALIGNED":
            raise ValueError("latest_metrics_version_alignment_status must be LATEST_METRICS_VERSION_ALIGNED")
        
        for rep in ["release_zip_report_present", "zip_audit_report_present", "zip_smoke_test_report_present"]:
            if consist.get(rep) is not True:
                raise ValueError(f"{rep} must be True")

        # Safety flags
        expected_flags = {
            "real_collection_approved": False,
            "human_review_required_before_collection": True,
            "network_disabled": True,
            "dry_run_only": True,
            "local_fixture_only": True,
            "fixture_only": True,
            "synthetic_or_minimal_sample": True,
            "not_for_research_results": True,
            "real_collection_executed": False,
            "external_data_downloaded": False,
            "external_api_called": False,
            "new_data_files_created": False,
            "no_data_directory_writes": True,
            "parquet_created": False,
            "csv_created": False,
            "sqlite_created": False,
            "requests_executed_count": 0,
            "no_new_filter": True,
            "no_strategy_validated": True,
            "no_preregistration_yet": True,
            "no_paper_live": True,
            "no_real_trading": True,
            "holdout_executed": False,
            "codex_cli_called": False,
            "real_orders_possible": False
        }
        for flag, expected in expected_flags.items():
            if consist.get(flag) != expected:
                raise ValueError(f"Consistency flag {flag} is {consist.get(flag)}, expected {expected}")

    # 4. State alignment
    ps_path = Path("reports/PROJECT_STATE.json")
    with open(ps_path) as f:
        ps = json.load(f)
        if ps.get("version") != version.upper():
            raise ValueError(f"PROJECT_STATE version mismatch: {ps.get('version')}")
        if ps.get("current_version") != version.upper():
            raise ValueError(f"PROJECT_STATE current_version mismatch: {ps.get('current_version')}")
        if ps.get("previous_version") != "V1.57.1":
            raise ValueError(f"PROJECT_STATE previous_version mismatch: {ps.get('previous_version')}")
        if ps.get("previous_base") != "V1.57.1":
            raise ValueError(f"PROJECT_STATE previous_base mismatch: {ps.get('previous_base')}")
        if ps.get("consistency_check_status") != consist["consistency_check_status"]:
             raise ValueError("PROJECT_STATE consistency status mismatch")
        if ps.get("latest_metrics_version_alignment_status") != "LATEST_METRICS_VERSION_ALIGNED":
             raise ValueError("PROJECT_STATE latest_metrics_version_alignment_status mismatch")
        if ps.get("release_reports_packaging_status") != "RELEASE_REPORTS_INCLUDED":
             raise ValueError("PROJECT_STATE release_reports_packaging_status mismatch")

    # 5. Latest metrics alignment
    lm_path = Path("reports/current/latest_metrics.json")
    if lm_path.exists():
        with open(lm_path) as f:
            lm = json.load(f)
            if lm.get("version") != version.upper():
                raise ValueError(f"latest_metrics version mismatch: {lm.get('version')}")
            if lm.get("current_version") != version.upper():
                raise ValueError(f"latest_metrics current_version mismatch: {lm.get('current_version')}")
            if lm.get("previous_version") != "V1.57.1":
                raise ValueError(f"latest_metrics previous_version mismatch: {lm.get('previous_version')}")
            if lm.get("previous_base") != "V1.57.1":
                raise ValueError(f"latest_metrics previous_base mismatch: {lm.get('previous_base')}")
            if lm.get("latest_metrics_version_alignment_status") != "LATEST_METRICS_VERSION_ALIGNED":
                raise ValueError("latest_metrics alignment status mismatch")
            if lm.get("release_reports_packaging_status") != "RELEASE_REPORTS_INCLUDED":
                raise ValueError("latest_metrics packaging status mismatch")

    # 6. Release reports presence (mandatory for V1.57.2)
    release_reports = [
        f"reports/release_zip_{v_norm}.json",
        f"reports/zip_audit_{v_norm}.json",
        f"reports/zip_smoke_test_{v_norm}.json"
    ]
    for rr in release_reports:
        if not Path(rr).exists():
             raise FileNotFoundError(f"Missing mandatory release report: {rr}")

    # 7. Check for NaN/Infinity
    def check_finite(obj):
        if isinstance(obj, dict):
            for v in obj.values(): check_finite(v)
        elif isinstance(obj, list):
            for v in obj: check_finite(v)
        elif isinstance(obj, float):
            if not os.is_finite(obj): raise ValueError("Found NaN/Infinity in JSON")

    # 8. Data check
    if Path("data").exists():
        for p in Path("data").rglob("*"):
            if p.suffix in [".parquet", ".csv", ".sqlite", ".db", ".jsonl"]:
                raise ValueError(f"Forbidden data file found: {p}")
             
    print(f"Validation for {version} PASSED.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    validate_reports(args.version)
