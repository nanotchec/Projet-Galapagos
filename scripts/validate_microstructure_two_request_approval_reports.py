import argparse
import json
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v1.73")
    args = parser.parse_args()

    v_norm = args.version.replace(".", "_").lower()
    reports_dir = Path("reports/research")
    summary_p = reports_dir / f"microstructure_two_request_approval_summary_{v_norm}.json"

    if not summary_p.exists():
        print(f"ERROR: Summary report {summary_p} not found")
        sys.exit(1)

    with open(summary_p) as f:
        summary = json.load(f)
    
    # 0. Version checks
    if summary.get("version") not in ["V1.73", "V1.73.1"]:
        print(f"ERROR: Expected version V1.73 or V1.73.1, got {summary.get('version')}")
        sys.exit(1)
    
    if summary.get("version") == "V1.73.1":
        if summary.get("previous_base") != "V1.73":
            print(f"ERROR: V1.73.1 must have previous_base V1.73, got {summary.get('previous_base')}")
            sys.exit(1)
        if summary.get("final_verdict") != "MICROSTRUCTURE_TWO_REQUEST_APPROVAL_INTAKE_VALIDATED":
            print(f"ERROR: V1.73.1 final_verdict must be VALIDATED")
            sys.exit(1)
        if not summary.get("approval_phrase_validated"):
            print("ERROR: V1.73.1 must have approval_phrase_validated = true")
            sys.exit(1)
    else:
        if summary.get("previous_base") != "V1.72":
            print(f"ERROR: Expected previous_base V1.72, got {summary.get('previous_base')}")
            sys.exit(1)

    # 1. Activity constraints (MUST BE ZERO in V1.73)
    if summary.get("requests_executed_count") != 0:
        print(f"ERROR: requests_executed_count must be 0")
        sys.exit(1)
    if summary.get("new_network_requests_executed_count") != 0:
        print(f"ERROR: new_network_requests_executed_count must be 0")
        sys.exit(1)
    if summary.get("external_api_called") is not False:
        print("ERROR: external_api_called must be False")
        sys.exit(1)
    if summary.get("new_external_api_called") is not False:
        print("ERROR: new_external_api_called must be False")
        sys.exit(1)
    if summary.get("network_enabled") is not False:
        print("ERROR: network_enabled must be False")
        sys.exit(1)

    # 2. Previous phase checks
    if summary.get("previous_one_request_review_passed") is not True:
        print("ERROR: previous_one_request_review_passed must be True")
        sys.exit(1)
    if summary.get("previous_requests_executed_count") != 1:
        print("ERROR: previous_requests_executed_count must be 1")
        sys.exit(1)
    if summary.get("previous_collection_expansion_approved") is not False:
        print("ERROR: previous_collection_expansion_approved must be False")
        sys.exit(1)
    if summary.get("previous_future_expansion_requires_new_human_approval") is not True:
        print("ERROR: previous_future_expansion_requires_new_human_approval must be True")
        sys.exit(1)

    # 3. Policy constraints
    if summary.get("max_request_count") != 2:
        print("ERROR: max_request_count must be 2")
        sys.exit(1)
    if summary.get("max_records_preview") != 20:
        print("ERROR: max_records_preview must be 20")
        sys.exit(1)

    # 4. Approval logic
    validated = summary.get("approval_phrase_validated")
    provided = summary.get("approval_phrase_provided")
    granted = summary.get("human_approval_granted")
    authorized = summary.get("v1_74_two_request_preflight_authorized")

    if validated and not provided:
        print("ERROR: approval_phrase_validated = true mais approval_phrase_provided != true")
        sys.exit(1)
    if granted and not validated:
        print("ERROR: human_approval_granted = true mais approval_phrase_validated != true")
        sys.exit(1)
    if authorized and not granted:
        print("ERROR: v1_74_two_request_preflight_authorized = true mais human_approval_granted != true")
        sys.exit(1)

    # 5. Safety constraints
    if summary.get("data_directory_writes_allowed") is True:
        print("ERROR: data_directory_writes_allowed must be False")
        sys.exit(1)
    if summary.get("new_data_files_created") is True:
        print("ERROR: new_data_files_created must be False")
        sys.exit(1)
    if summary.get("no_data_directory_writes") is not True:
        print("ERROR: no_data_directory_writes must be True")
        sys.exit(1)
    if summary.get("strategy_link_allowed") is True:
        print("ERROR: strategy_link_allowed must be False")
        sys.exit(1)
    if summary.get("trading_allowed") is True:
        print("ERROR: trading_allowed must be False")
        sys.exit(1)
    if summary.get("no_real_trading") is not True:
        print("ERROR: no_real_trading must be True")
        sys.exit(1)
    if summary.get("real_orders_possible") is True:
        print("ERROR: real_orders_possible must be False")
        sys.exit(1)

    # 6. Artifact checks
    required_stems = [
        "microstructure_two_request_approval_input_guard",
        "microstructure_two_request_approval_phrase_validator",
        "microstructure_two_request_authorization_policy",
        "microstructure_v1_74_execution_plan",
        "microstructure_two_request_approval_decision",
        "microstructure_two_request_approval_recommendation",
        "microstructure_two_request_approval_summary",
        "microstructure_two_request_approval_consistency_check",
        "v1_73_recommendation"
    ]
    for stem in required_stems:
        if stem == "v1_73_recommendation":
            json_p = reports_dir / f"{stem}.json"
        else:
            json_p = reports_dir / f"{stem}_{v_norm}.json"

        if not json_p.exists():
            print(f"ERROR: Missing report {json_p.name}")
            sys.exit(1)

    print(f"SUCCESS: V1.73 reports validated for {args.version}")

if __name__ == "__main__":
    main()
