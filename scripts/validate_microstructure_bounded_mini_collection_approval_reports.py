import json
import sys
from pathlib import Path

def main():
    version_arg = "V1.76"
    if len(sys.argv) > 2 and sys.argv[1] == "--version":
        version_arg = sys.argv[2].upper()

    v_norm = version_arg.replace(".", "_").lower()
    root = Path.cwd()
    summary_p = root / f"reports/research/microstructure_bounded_mini_collection_approval_summary_{v_norm}.json"

    if not summary_p.exists():
        print(f"ERROR: Summary not found at {summary_p}")
        sys.exit(1)

    with open(summary_p) as f:
        summary = json.load(f)
    
    # 0. Version checks
    expected_prev = "V1.75" if version_arg == "V1.76" else "V1.76"
    if summary.get("version") != version_arg:
        print(f"ERROR: Expected version {version_arg}, got {summary.get('version')}")
        sys.exit(1)
    if summary.get("previous_base") != expected_prev:
        print(f"ERROR: Expected previous_base {expected_prev}, got {summary.get('previous_base')}")
        sys.exit(1)

    # 1. Activity constraints (MUST BE ZERO in V1.76)
    if summary.get("requests_executed_count") != 0:
        print(f"ERROR: requests_executed_count {summary.get('requests_executed_count')} != 0")
        sys.exit(1)
    
    if summary.get("new_network_requests_executed_count") != 0:
        print("ERROR: new_network_requests_executed_count must be 0")
        sys.exit(1)

    if summary.get("external_api_called") is not False:
        print("ERROR: external_api_called must be false")
        sys.exit(1)

    if summary.get("network_enabled") is not False:
        print("ERROR: network_enabled must be false")
        sys.exit(1)

    # 2. Authorization limits
    if summary.get("max_request_count") != 10:
        print(f"ERROR: max_request_count {summary.get('max_request_count')} != 10")
        sys.exit(1)

    if summary.get("max_records_preview_total") != 100:
        print(f"ERROR: max_records_preview_total {summary.get('max_records_preview_total')} != 100")
        sys.exit(1)

    # 3. Context certification
    if summary.get("previous_two_request_review_passed") is not True:
        print("ERROR: previous_two_request_review_passed must be true")
        sys.exit(1)

    if summary.get("previous_requests_executed_count") != 2:
        print(f"ERROR: previous_requests_executed_count {summary.get('previous_requests_executed_count')} != 2")
        sys.exit(1)

    if summary.get("previous_bounded_mini_collection_approved") is not False:
        print("ERROR: previous_bounded_mini_collection_approved must be false")
        sys.exit(1)

    if summary.get("previous_future_mini_collection_requires_new_human_approval") is not True:
        print("ERROR: previous_future_mini_collection_requires_new_human_approval must be true")
        sys.exit(1)

    # 4. Phrase logic
    valid = summary.get("approval_phrase_validated")
    provided = summary.get("approval_phrase_provided")
    granted = summary.get("human_approval_granted")
    authorized = summary.get("v1_77_bounded_mini_collection_authorized")

    if valid is True and provided is not True:
        print("ERROR: phrase validated but not provided")
        sys.exit(1)

    if granted is True and valid is not True:
        print("ERROR: approval granted but phrase not validated")
        sys.exit(1)

    if authorized is True and granted is not True:
        print("ERROR: authorized but approval not granted")
        sys.exit(1)

    if version_arg == "V1.76.1":
        if not authorized:
            print("ERROR: V1.76.1 must have authorization granted")
            sys.exit(1)
        if not granted:
            print("ERROR: V1.76.1 must have human approval granted")
            sys.exit(1)
        if not valid:
            print("ERROR: V1.76.1 must have phrase validated")
            sys.exit(1)

    # 5. Data writes & Business
    if summary.get("no_data_directory_writes") is not True:
        print("ERROR: no_data_directory_writes must be true")
        sys.exit(1)

    for fmt in ["parquet", "csv", "sqlite", "jsonl", "db"]:
        if summary.get(f"{fmt}_created") is not False:
            print(f"ERROR: {fmt}_created must be false")
            sys.exit(1)

    if summary.get("dataset_created") is not False:
        print("ERROR: dataset_created must be false")
        sys.exit(1)

    if summary.get("bounded_mini_collection_executed") is not False:
        print("ERROR: bounded_mini_collection_executed must be false")
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

    # 6. Machine specific paths
    if summary.get("machine_specific_paths_found"):
        print("ERROR: Machine specific paths found")
        sys.exit(1)

    print(f"SUCCESS: {version_arg} reports validated")

if __name__ == "__main__":
    main()
