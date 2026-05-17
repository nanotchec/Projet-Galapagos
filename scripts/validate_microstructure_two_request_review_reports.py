import json
import sys
from pathlib import Path

def main():
    version_arg = "V1.75"
    if len(sys.argv) > 2 and sys.argv[1] == "--version":
        version_arg = sys.argv[2].upper()

    v_norm = version_arg.replace(".", "_").lower()
    root = Path.cwd()
    summary_p = root / f"reports/research/microstructure_two_request_review_summary_{v_norm}.json"

    if not summary_p.exists():
        print(f"ERROR: Summary not found at {summary_p}")
        sys.exit(1)

    with open(summary_p) as f:
        summary = json.load(f)
    
    # 0. Version checks
    if summary.get("version") != "V1.75":
        print(f"ERROR: Expected version V1.75, got {summary.get('version')}")
        sys.exit(1)
    if summary.get("previous_base") != "V1.74":
        print(f"ERROR: Expected previous_base V1.74, got {summary.get('previous_base')}")
        sys.exit(1)

    # 1. Activity constraints (MUST BE ZERO in V1.75)
    if summary.get("requests_executed_count") != 0:
        print(f"ERROR: requests_executed_count {summary.get('requests_executed_count')} != 0")
        sys.exit(1)
    
    if summary.get("new_network_requests_executed_count") != 0:
        print("ERROR: new_network_requests_executed_count must be 0")
        sys.exit(1)

    if summary.get("external_api_called") is not False:
        print("ERROR: external_api_called must be false")
        sys.exit(1)

    # 2. Previous preflight certification
    if summary.get("previous_requests_executed_count") != 2:
        print(f"ERROR: previous_requests_executed_count {summary.get('previous_requests_executed_count')} != 2")
        sys.exit(1)

    if summary.get("previous_records_preview_count_total", 0) > 20:
        print("ERROR: previous_records_preview_count_total > 20")
        sys.exit(1)

    if summary.get("previous_records_preview_count_total_lte_20") is not True:
        print("ERROR: previous_records_preview_count_total_lte_20 must be true")
        sys.exit(1)

    if summary.get("previous_records_preview_count_per_request_lte_10") is not True:
        print("ERROR: previous_records_preview_count_per_request_lte_10 must be true")
        sys.exit(1)

    if summary.get("previous_response_comparison_created") is not True:
        print("ERROR: previous_response_comparison_created must be true")
        sys.exit(1)

    if summary.get("previous_endpoint_authentication_required") is not False:
        print("ERROR: previous_endpoint_authentication_required must be false")
        sys.exit(1)

    if summary.get("previous_secrets_used") is not False:
        print("ERROR: previous_secrets_used must be false")
        sys.exit(1)

    # 3. Gate constraints
    if summary.get("bounded_mini_collection_approved") is not False:
        print("ERROR: bounded_mini_collection_approved must be false")
        sys.exit(1)

    if summary.get("future_mini_collection_requires_new_human_approval") is not True:
        print("ERROR: future_mini_collection_requires_new_human_approval must be true")
        sys.exit(1)

    if summary.get("max_future_request_count_without_new_approval") != 0:
        print("ERROR: max_future_request_count_without_new_approval must be 0")
        sys.exit(1)

    # 4. Data writes & Business
    if summary.get("no_data_directory_writes") is not True:
        print("ERROR: no_data_directory_writes must be true")
        sys.exit(1)

    if summary.get("dataset_created") is not False:
        print("ERROR: dataset_created must be false")
        sys.exit(1)

    if summary.get("strategy_link_allowed") is not False:
        print("ERROR: strategy_link_allowed must be false")
        sys.exit(1)

    if summary.get("trading_allowed") is not False:
        print("ERROR: trading_allowed must be false")
        sys.exit(1)

    if summary.get("real_collection_approved") is not False:
        print("ERROR: real_collection_approved must be false")
        sys.exit(1)

    if summary.get("real_orders_possible") is not False:
        print("ERROR: real_orders_possible must be false")
        sys.exit(1)

    # 5. Machine specific paths
    if summary.get("machine_specific_paths_found"):
        print("ERROR: Machine specific paths found")
        sys.exit(1)

    print(f"SUCCESS: V1.75 reports validated for {version_arg}")

if __name__ == "__main__":
    main()
