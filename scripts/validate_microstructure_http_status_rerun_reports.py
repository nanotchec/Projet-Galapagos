import json
import sys
from pathlib import Path

def main():
    version_arg = "V1.79"
    if len(sys.argv) > 2 and sys.argv[1] == "--version":
        version_arg = sys.argv[2].upper()

    v_norm = version_arg.replace(".", "_").lower()
    root = Path.cwd()
    summary_p = root / f"reports/research/microstructure_http_status_rerun_summary_{v_norm}.json"

    if not summary_p.exists():
        print(f"ERROR: Summary not found at {summary_p}")
        sys.exit(1)

    with open(summary_p) as f:
        summary = json.load(f)
    
    # 0. Version checks
    if summary.get("version") != "V1.79":
        print(f"ERROR: Expected version V1.79, got {summary.get('version')}")
        sys.exit(1)
    if summary.get("previous_base") != "V1.78":
        print(f"ERROR: Expected previous_base V1.78, got {summary.get('previous_base')}")
        sys.exit(1)

    # 1. Activity constraints
    if summary.get("requests_executed_count", 0) > 10:
        print(f"ERROR: requests_executed_count {summary.get('requests_executed_count')} > 10")
        sys.exit(1)
    if summary.get("max_request_count") != 10:
        print("ERROR: max_request_count must be 10")
        sys.exit(1)
    if summary.get("request_retry_count") != 0:
        print("ERROR: request_retry_count must be 0")
        sys.exit(1)
    if summary.get("pagination_used") is not False:
        print("ERROR: pagination_used must be false")
        sys.exit(1)
    if summary.get("authenticated_request_allowed") is not False:
        print("ERROR: authenticated_request_allowed must be false")
        sys.exit(1)
    if summary.get("secrets_used") is not False:
        print("ERROR: secrets_used must be false")
        sys.exit(1)

    # 2. Data writes & Dataset
    if summary.get("data_directory_writes_allowed") is not False:
        print("ERROR: data_directory_writes_allowed must be false")
        sys.exit(1)
    if summary.get("new_data_files_created") is not False:
        print("ERROR: new_data_files_created must be false")
        sys.exit(1)
    if summary.get("no_data_directory_writes") is not True:
        print("ERROR: no_data_directory_writes must be true")
        sys.exit(1)
    if summary.get("dataset_created") is not False:
        print("ERROR: dataset_created must be false")
        sys.exit(1)

    # 3. Strategy & Trading
    if summary.get("trading_allowed") is not False:
        print("ERROR: trading_allowed must be false")
        sys.exit(1)
    if summary.get("no_strategy_validated") is not True:
        print("ERROR: no_strategy_validated must be true")
        sys.exit(1)
    if summary.get("no_paper_live") is not True:
        print("ERROR: no_paper_live must be true")
        sys.exit(1)
    if summary.get("no_real_trading") is not True:
        print("ERROR: no_real_trading must be true")
        sys.exit(1)
    if summary.get("real_collection_approved") is not False:
        print("ERROR: real_collection_approved must be false")
        sys.exit(1)
    if summary.get("real_orders_possible") is not False:
        print("ERROR: real_orders_possible must be false")
        sys.exit(1)

    # 4. Preview constraints
    if summary.get("records_preview_count_total", 0) > 100:
        print("ERROR: records_preview_count_total > 100")
        sys.exit(1)
    if summary.get("records_preview_count_per_request_lte_10") is not True:
        print("ERROR: records_preview_count_per_request_lte_10 must be true")
        sys.exit(1)

    # 5. Status Capture Constraints (Hardening)
    success_count = summary.get("successful_response_count", 0)
    status_codes = summary.get("response_status_codes", [])
    
    if success_count > 0:
        if not status_codes or None in status_codes:
            print("ERROR: response_status_codes contains None while success_count > 0")
            sys.exit(1)
        if summary.get("response_status_codes_all_present") is not True:
            print("ERROR: response_status_codes_all_present must be true when success > 0")
            sys.exit(1)

    if "PASSED" in summary.get("final_verdict", ""):
        if summary.get("response_status_codes_all_present") is not True:
            print("ERROR: PASSED verdict requires response_status_codes_all_present=true")
            sys.exit(1)
        if summary.get("response_status_codes_none_present") is not False:
            print("ERROR: PASSED verdict requires response_status_codes_none_present=false")
            sys.exit(1)
        if summary.get("response_status_codes_all_success") is not True:
            print("ERROR: PASSED verdict requires response_status_codes_all_success=true")
            sys.exit(1)

    # 6. Per Request Records
    records = summary.get("per_request_status_records", [])
    if summary.get("requests_executed_count", 0) > 0 and not records:
        print("ERROR: per_request_status_records is empty while requests were executed")
        sys.exit(1)
    
    for r in records:
        if r.get("success_flag") is True:
            if r.get("status_code") is None or not isinstance(r.get("status_code"), int):
                print(f"ERROR: Request {r.get('request_index')} has success_flag=True but invalid status_code")
                sys.exit(1)
            if not (200 <= r.get("status_code") < 300):
                print(f"ERROR: Request {r.get('request_index')} has success_flag=True but non-2xx status_code")
                sys.exit(1)

    print(f"SUCCESS: {version_arg} reports validated")

if __name__ == "__main__":
    main()
