import argparse
import json
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v1.72")
    args = parser.parse_args()

    v_norm = args.version.replace(".", "_").lower()
    reports_dir = Path("reports/research")
    summary_p = reports_dir / f"microstructure_one_request_review_summary_{v_norm}.json"

    if not summary_p.exists():
        print(f"ERROR: Summary report {summary_p} not found")
        sys.exit(1)

    with open(summary_p) as f:
        summary = json.load(f)
    
    # 0. Version checks
    if summary.get("version") != "V1.72":
        print(f"ERROR: Expected version V1.72, got {summary.get('version')}")
        sys.exit(1)
    if summary.get("previous_base") != "V1.71":
        print(f"ERROR: Expected previous_base V1.71, got {summary.get('previous_base')}")
        sys.exit(1)

    # 1. Activity constraints (MUST BE ZERO in V1.72)
    if summary.get("requests_executed_count") != 0:
        print(f"ERROR: requests_executed_count must be 0, got {summary.get('requests_executed_count')}")
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

    # 2. Previous phase checks
    if summary.get("previous_requests_executed_count") != 1:
        print(f"ERROR: previous_requests_executed_count must be 1, got {summary.get('previous_requests_executed_count')}")
        sys.exit(1)
    if summary.get("previous_records_preview_count", 0) > 10:
        print(f"ERROR: previous_records_preview_count too high")
        sys.exit(1)
    if summary.get("previous_endpoint_authentication_required") is not False:
        print("ERROR: previous_endpoint_authentication_required must be False")
        sys.exit(1)
    if summary.get("previous_secrets_used") is not False:
        print("ERROR: previous_secrets_used must be False")
        sys.exit(1)

    # 3. Expansion constraints
    if summary.get("collection_expansion_approved") is not False:
        print("ERROR: collection_expansion_approved must be False")
        sys.exit(1)
    if summary.get("future_expansion_requires_new_human_approval") is not True:
        print("ERROR: future_expansion_requires_new_human_approval must be True")
        sys.exit(1)
    if summary.get("max_future_request_count_without_new_approval") != 0:
        print("ERROR: max_future_request_count_without_new_approval must be 0")
        sys.exit(1)

    # 4. Safety constraints
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

    # 5. Artifact checks
    required_stems = [
        "microstructure_one_request_review_input_guard",
        "microstructure_request_limit_review",
        "microstructure_endpoint_review",
        "microstructure_response_preview_review",
        "microstructure_no_data_write_review",
        "microstructure_no_strategy_linkage_review",
        "microstructure_expansion_readiness_gate",
        "microstructure_one_request_review_decision",
        "microstructure_one_request_review_recommendation",
        "microstructure_one_request_review_summary",
        "microstructure_one_request_review_consistency_check",
        "v1_72_recommendation"
    ]
    for stem in required_stems:
        if stem == "v1_72_recommendation":
            json_p = reports_dir / f"{stem}.json"
        else:
            json_p = reports_dir / f"{stem}_{v_norm}.json"

        if not json_p.exists():
            print(f"ERROR: Missing report {json_p.name}")
            sys.exit(1)

    print(f"SUCCESS: V1.72 reports validated for {args.version}")

if __name__ == "__main__":
    main()
