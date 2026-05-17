import json
import sys
from pathlib import Path

def main():
    version_arg = "V1.77.1"
    if len(sys.argv) > 2 and sys.argv[1] == "--version":
        version_arg = sys.argv[2].upper()

    v_norm = version_arg.replace(".", "_").lower()
    root = Path.cwd()
    summary_p = root / f"reports/research/microstructure_bounded_reporting_fix_summary_{v_norm}.json"

    if not summary_p.exists():
        print(f"ERROR: Summary not found at {summary_p}")
        sys.exit(1)

    with open(summary_p) as f:
        summary = json.load(f)
    
    # 0. Version checks
    if summary.get("version") != "V1.77.1":
        print(f"ERROR: Expected version V1.77.1, got {summary.get('version')}")
        sys.exit(1)
    if summary.get("previous_base") != "V1.77":
        print(f"ERROR: Expected previous_base V1.77, got {summary.get('previous_base')}")
        sys.exit(1)

    # 1. Reporting Fix Checks
    prev_success = summary.get("previous_successful_response_count", 0)
    prev_codes = summary.get("previous_response_status_codes", [])
    
    if prev_success > 0 and None in prev_codes:
        if summary.get("previous_status_reporting_incomplete") is not True:
            print("ERROR: previous_status_reporting_incomplete must be true when codes contain None")
            sys.exit(1)

    if summary.get("response_status_codes_none_present") is not False:
        print("ERROR: response_status_codes_none_present must be false")
        sys.exit(1)

    if summary.get("response_status_codes_available") is True:
        if not summary.get("response_status_codes"):
            print("ERROR: response_status_codes_available is true but list is empty")
            sys.exit(1)

    if summary.get("response_status_codes_all_present") is True:
        if None in summary.get("response_status_codes", []):
            print("ERROR: response_status_codes_all_present is true but list contains None")
            sys.exit(1)

    if summary.get("response_status_codes_all_success") is True:
        codes = summary.get("response_status_codes", [])
        if any(c < 200 or c >= 300 for c in codes):
            print("ERROR: response_status_codes_all_success is true but non-2xx code found")
            sys.exit(1)

    if "PASSED" in summary.get("final_verdict", ""):
        if summary.get("response_status_codes_all_present") is not True:
            print("ERROR: PASSED verdict requires response_status_codes_all_present=true")
            sys.exit(1)

    # 2. Activity constraints
    if summary.get("requests_executed_count") != 0:
        print("ERROR: requests_executed_count must be 0 for V1.77.1")
        sys.exit(1)
    
    if summary.get("new_network_requests_executed_count") != 0:
        print("ERROR: new_network_requests_executed_count must be 0")
        sys.exit(1)

    if summary.get("external_api_called") is not False:
        print("ERROR: external_api_called must be false")
        sys.exit(1)

    if summary.get("bounded_mini_collection_executed") is not False:
        print("ERROR: bounded_mini_collection_executed must be false for V1.77.1")
        sys.exit(1)

    # 3. Data writes & Dataset
    if summary.get("no_data_directory_writes") is not True:
        print("ERROR: no_data_directory_writes must be true")
        sys.exit(1)

    if summary.get("dataset_created") is not False:
        print("ERROR: dataset_created must be false")
        sys.exit(1)

    # 4. Strategy & Trading
    if summary.get("no_real_trading") is not True:
        print("ERROR: no_real_trading must be true")
        sys.exit(1)

    if summary.get("real_orders_possible") is not False:
        print("ERROR: real_orders_possible must be false")
        sys.exit(1)

    print(f"SUCCESS: {version_arg} reports validated")

if __name__ == "__main__":
    main()
