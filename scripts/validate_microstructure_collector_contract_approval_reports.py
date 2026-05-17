from __future__ import annotations
import argparse
import json
from pathlib import Path

def validate_reports(version: str):
    v_norm = version.lower().replace(".", "_")
    root = Path("reports/research")
    
    VERDICT = "MICROSTRUCTURE_COLLECTOR_CONTRACT_PARTIAL"
    NEXT_STEP = "refine adapter field coverage before offline review"
    
    required_json = [
        f"microstructure_contract_input_guard_{v_norm}.json",
        f"microstructure_contract_approval_checklist_{v_norm}.json",
        f"microstructure_required_field_coverage_{v_norm}.json",
        f"microstructure_adapter_contract_completeness_{v_norm}.json",
        f"microstructure_timestamp_policy_approval_{v_norm}.json",
        f"microstructure_manifest_contract_approval_{v_norm}.json",
        f"microstructure_fixture_coverage_approval_{v_norm}.json",
        f"microstructure_network_safety_approval_{v_norm}.json",
        f"microstructure_data_write_safety_approval_{v_norm}.json",
        f"microstructure_contract_approval_decision_{v_norm}.json",
        f"microstructure_contract_recommendation_{v_norm}.json",
        f"microstructure_contract_approval_summary_{v_norm}.json",
        f"microstructure_contract_approval_consistency_check_{v_norm}.json",
        f"{v_norm}_recommendation.json"
    ]
    
    # 1. Check JSON files presence and validity
    for f_name in required_json:
        path = root / f_name
        if not path.exists():
            raise FileNotFoundError(f"Missing mandatory JSON report: {path}")
        
        with open(path) as f:
            try:
                data = json.load(f)
            except Exception as e:
                raise ValueError(f"Invalid JSON file {path}: {e}")
            
            # Check for NaN / Infinity
            content = json.dumps(data)
            if "NaN" in content or "Infinity" in content:
                raise ValueError(f"JSON file {path} contains NaN or Infinity")

    # 2. Check MD files presence
    for f_name in required_json:
        md_path = root / f_name.replace(".json", ".md")
        if not md_path.exists():
            raise FileNotFoundError(f"Missing mandatory MD report: {md_path}")

    # 3. Check final doc
    doc_path = Path("docs") / f"microstructure_collector_contract_approval_{v_norm}.md"
    if not doc_path.exists():
        raise FileNotFoundError(f"Missing mandatory final documentation: {doc_path}")

    # 4. Deep validation of consistency check
    consist_path = root / f"microstructure_contract_approval_consistency_check_{v_norm}.json"
    with open(consist_path) as f:
        consist = json.load(f)
        if consist.get("version") != version.upper():
            raise ValueError(f"Consistency check version mismatch: {consist.get('version')}")
        if consist.get("previous_base") != "V1.56":
            raise ValueError(f"Consistency check previous_base mismatch: {consist.get('previous_base')}")
        if consist.get("issues") != []:
            raise ValueError(f"Consistency check issues found: {consist.get('issues')}")
        if consist.get("consistency_check_status") != "MICROSTRUCTURE_CONTRACT_APPROVAL_REPORTS_CONSISTENT_INFRASTRUCTURE_ONLY":
            raise ValueError(f"Invalid consistency_check_status: {consist.get('consistency_check_status')}")
        
        if consist.get("project_state_verdict_aligned") != True:
            raise ValueError("project_state_verdict_aligned != true")
        if consist.get("latest_metrics_verdict_aligned") != True:
            raise ValueError("latest_metrics_verdict_aligned != true")
        if consist.get("latest_summary_verdict_aligned") != True:
            raise ValueError("latest_summary_verdict_aligned != true")
        if consist.get("stale_v1_55_verdict_removed") != True:
            raise ValueError("stale_v1_55_verdict_removed != true")
        if consist.get("required_reports_present") != True:
            raise ValueError("required_reports_present != true")
        if consist.get("required_markdown_reports_present") != True:
            raise ValueError("required_markdown_reports_present != true")
        if consist.get("project_state_aligned") != True:
            raise ValueError("project_state_aligned != true")
        if consist.get("latest_metrics_aligned") != True:
            raise ValueError("latest_metrics_aligned != true")
        if consist.get("latest_summary_aligned") != True:
            raise ValueError("latest_summary_aligned != true")

        # Safety flags
        expected_values = {
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
            "real_orders_possible": False,
            "contract_ready_for_offline_review": False,
            "required_fields_covered": False,
            "missing_required_fields": 8
        }
        for flag, expected in expected_values.items():
            if consist.get(flag) != expected:
                raise ValueError(f"Consistency check flag {flag} is {consist.get(flag)}, expected {expected}")

    # 5. Project State validation
    ps_path = Path("reports/PROJECT_STATE.json")
    with open(ps_path) as f:
        ps = json.load(f)
        if ps.get("version") != version.upper():
            raise ValueError(f"PROJECT_STATE version mismatch: {ps.get('version')}")
        if ps.get("final_verdict") != VERDICT:
            raise ValueError(f"PROJECT_STATE final_verdict mismatch: {ps.get('final_verdict')}")
        if ps.get("recommended_next_step") != NEXT_STEP:
            raise ValueError(f"PROJECT_STATE recommended_next_step mismatch: {ps.get('recommended_next_step')}")
        if ps.get("final_verdict") == "MICROSTRUCTURE_ADAPTER_FIXTURE_TESTS_READY":
            raise ValueError("PROJECT_STATE contains STALE V1.55 verdict")
        
        for flag, expected in expected_values.items():
            if ps.get(flag) != expected:
                 raise ValueError(f"PROJECT_STATE flag {flag} is {ps.get(flag)}, expected {expected}")

    # 6. Latest Metrics validation
    lm_path = Path("reports/current/latest_metrics.json")
    with open(lm_path) as f:
        lm = json.load(f)
        if lm.get("version") != version.upper():
            raise ValueError(f"latest_metrics version mismatch: {lm.get('version')}")
        if lm.get("final_verdict") != VERDICT:
            raise ValueError(f"latest_metrics final_verdict mismatch: {lm.get('final_verdict')}")
        if lm.get("recommended_next_step") != NEXT_STEP:
            raise ValueError(f"latest_metrics recommended_next_step mismatch: {lm.get('recommended_next_step')}")
        if lm.get("final_verdict") == "MICROSTRUCTURE_ADAPTER_FIXTURE_TESTS_READY":
            raise ValueError("latest_metrics contains STALE V1.55 verdict")

        for flag, expected in expected_values.items():
            if lm.get(flag) != expected:
                 raise ValueError(f"latest_metrics flag {flag} is {lm.get(flag)}, expected {expected}")

    print(f"Validation for {version} PASSED.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    validate_reports(args.version)
