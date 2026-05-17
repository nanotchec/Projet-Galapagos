import argparse
import json
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v1.70.2")
    args = parser.parse_args()

    v_norm = args.version.replace(".", "_").lower()
    root = Path.cwd()
    reports_dir = root / "reports/research"
    
    summary_p = reports_dir / f"microstructure_human_approval_summary_{v_norm}.json"
    if not summary_p.exists():
        print(f"ERROR: Missing summary at {summary_p}")
        sys.exit(1)
    
    with open(summary_p) as f:
        summary = json.load(f)
    
    # 0. Version checks
    if summary.get("version") != "V1.70.2":
        print(f"ERROR: Expected version V1.70.2, got {summary.get('version')}")
        sys.exit(1)
    if summary.get("previous_base") != "V1.70.1":
        print(f"ERROR: Expected previous_base V1.70.1, got {summary.get('previous_base')}")
        sys.exit(1)

    # 1. Approval checks
    if summary.get("approval_phrase_provided") != True:
        print("ERROR: approval_phrase_provided must be True")
        sys.exit(1)
    if summary.get("approval_phrase_validated") != True:
        print("ERROR: approval_phrase_validated must be True")
        sys.exit(1)
    if summary.get("human_approval_granted") != True:
        print("ERROR: human_approval_granted must be True")
        sys.exit(1)
    if summary.get("v1_71_network_preflight_authorized") != True:
        print("ERROR: v1_71_network_preflight_authorized must be True")
        sys.exit(1)
    if summary.get("v1_71_must_remain_one_request") != True:
        print("ERROR: v1_71_must_remain_one_request must be True")
        sys.exit(1)
    if summary.get("v1_71_reports_only") != True:
        print("ERROR: v1_71_reports_only must be True")
        sys.exit(1)
    if summary.get("v1_71_no_data_directory_writes") != True:
        print("ERROR: v1_71_no_data_directory_writes must be True")
        sys.exit(1)
    if summary.get("v1_71_no_trading") != True:
        print("ERROR: v1_71_no_trading must be True")
        sys.exit(1)

    # 2. Safety constraints
    expected_bools = {
        "network_enabled": False,
        "network_disabled": True,
        "tiny_network_preflight_command_executed": False,
        "tiny_network_collection_executed": False,
        "real_collection_executed": False,
        "real_collection_approved": False,
        "requests_executed_count": 0,
        "external_api_called": False,
        "external_data_downloaded": False,
        "new_data_files_created": False,
        "no_data_directory_writes": True,
        "parquet_created": False,
        "csv_created": False,
        "sqlite_created": False,
        "jsonl_created": False,
        "db_created": False,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "codex_cli_called": False,
        "real_orders_possible": False,
        "max_request_count": 1,
        "output_scope": "reports_only",
        "data_directory_writes_allowed": False,
        "trading_allowed": False,
        "strategy_link_allowed": False,
        "approval_intake_only": True
    }
    
    for k, v in expected_bools.items():
        if summary.get(k) != v:
            print(f"ERROR: Safety check failed for {k}. Expected {v}, got {summary.get(k)}")
            sys.exit(1)

    # 2. Logic consistency
    if summary.get("approval_phrase_validated") and not summary.get("approval_phrase_provided"):
        print("ERROR: approval_phrase_validated is True but approval_phrase_provided is False")
        sys.exit(1)
    if summary.get("human_approval_granted") and not summary.get("approval_phrase_validated"):
        print("ERROR: human_approval_granted is True but approval_phrase_validated is False")
        sys.exit(1)
    if summary.get("v1_71_network_preflight_authorized") and not summary.get("human_approval_granted"):
        print("ERROR: v1_71_network_preflight_authorized is True but human_approval_granted is False")
        sys.exit(1)

    # 3. Required reports
    required_stems = [
        "microstructure_human_approval_input_guard",
        "microstructure_approval_phrase_validator",
        "microstructure_approval_intake_policy",
        "microstructure_preflight_authorization_record",
        "microstructure_v1_71_execution_plan",
        "microstructure_human_approval_decision",
        "microstructure_human_approval_recommendation",
        "microstructure_human_approval_summary",
        "microstructure_human_approval_consistency_check",
        "v1_70_2_recommendation"
    ]
    for stem in required_stems:
        if stem == "v1_70_2_recommendation":
            json_p = reports_dir / f"{stem}.json"
            md_p = reports_dir / f"{stem}.md"
        else:
            json_p = reports_dir / f"{stem}_{v_norm}.json"
            md_p = reports_dir / f"{stem}_{v_norm}.md"

        if not json_p.exists():
            print(f"ERROR: Missing report {json_p.name}")
            sys.exit(1)
        if not md_p.exists():
            print(f"ERROR: Missing report {md_p.name}")
            sys.exit(1)

    # 4. Final verification
    forbidden_verdict_terms = ["VALIDATED_FOR_REAL_TRADING", "APPROVAL_GRANTED_FOR_LIVE"]
    verdict = summary.get("final_verdict", "")
    for term in forbidden_verdict_terms:
        if term in verdict:
            print(f"ERROR: Forbidden term '{term}' in final_verdict")
            sys.exit(1)

    print(f"SUCCESS: V1.70 reports validated for {args.version}")

if __name__ == "__main__":
    main()
