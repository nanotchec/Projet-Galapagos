import json
import sys
from pathlib import Path

def main():
    version_arg = "V1.80"
    if len(sys.argv) > 2 and sys.argv[1] == "--version":
        version_arg = sys.argv[2].upper().replace("_", ".")

    v_norm = version_arg.replace(".", "_").lower()
    root = Path.cwd()
    summary_p = root / f"reports/research/microstructure_data_contract_readiness_summary_{v_norm}.json"

    if not summary_p.exists():
        print(f"ERROR: Summary not found at {summary_p}")
        sys.exit(1)

    with open(summary_p) as f:
        summary = json.load(f)
    
    # 0. Version checks
    if summary.get("version") != "V1.80":
        print(f"ERROR: Expected version V1.80, got {summary.get('version')}")
        sys.exit(1)

    # 1. Review V1.79 invariants
    if summary.get("v1_79_successful_response_count") != 10:
        print(f"ERROR: V1.79 success count {summary.get('v1_79_successful_response_count')} != 10")
        sys.exit(1)
    if summary.get("v1_79_response_status_codes_count") != 10:
        print(f"ERROR: V1.79 status codes count {summary.get('v1_79_response_status_codes_count')} != 10")
        sys.exit(1)
    if summary.get("v1_79_response_status_codes_none_present") is not False:
        print("ERROR: V1.79 response_status_codes_none_present must be false")
        sys.exit(1)
    if summary.get("v1_79_response_status_codes_all_present") is not True:
        print("ERROR: V1.79 response_status_codes_all_present must be true")
        sys.exit(1)
    if summary.get("v1_79_response_status_codes_all_success") is not True:
        print("ERROR: V1.79 response_status_codes_all_success must be true")
        sys.exit(1)
    if summary.get("v1_79_max_request_count") != 10:
        print("ERROR: V1.79 max_request_count must be 10")
        sys.exit(1)
    if summary.get("v1_79_request_retry_count") != 0:
        print("ERROR: V1.79 request_retry_count must be 0")
        sys.exit(1)
    if summary.get("v1_79_pagination_used") is not False:
        print("ERROR: V1.79 pagination_used must be false")
        sys.exit(1)
    if summary.get("v1_79_no_data_directory_writes") is not True:
        print("ERROR: V1.79 no_data_directory_writes must be true")
        sys.exit(1)
    if summary.get("v1_79_dataset_created") is not False:
        print("ERROR: V1.79 dataset_created must be false")
        sys.exit(1)

    # 2. V1.80 invariants (NO NETWORK, NO DATA WRITE)
    if summary.get("network_executed") is not False:
        print("ERROR: network_executed must be false")
        sys.exit(1)
    if summary.get("new_network_requests_executed") is not False:
        print("ERROR: new_network_requests_executed must be false")
        sys.exit(1)
    if summary.get("data_directory_writes_allowed") is not False:
        print("ERROR: data_directory_writes_allowed must be false")
        sys.exit(1)
    if summary.get("new_data_files_created") is not False:
        print("ERROR: new_data_files_created must be false")
        sys.exit(1)
    if summary.get("no_data_directory_writes") is not True:
        print("ERROR: no_data_directory_writes must be true")
        sys.exit(1)
    if summary.get("parquet_created") is not False:
        print("ERROR: parquet_created must be false")
        sys.exit(1)
    if summary.get("dataset_created") is not False:
        print("ERROR: dataset_created must be false")
        sys.exit(1)
    if summary.get("secrets_used") is not False:
        print("ERROR: secrets_used must be false")
        sys.exit(1)
    if summary.get("trading_allowed") is not False:
        print("ERROR: trading_allowed must be false")
        sys.exit(1)
    if summary.get("real_orders_possible") is not False:
        print("ERROR: real_orders_possible must be false")
        sys.exit(1)

    # 3. Approval Gate V1.81 (Must be False)
    if summary.get("human_approval_granted") is not False:
        print("ERROR: human_approval_granted must be false in V1.80")
        sys.exit(1)
    if summary.get("v1_81_authorized") is not False:
        print("ERROR: v1_81_authorized must be false in V1.80")
        sys.exit(1)

    print(f"SUCCESS: {version_arg} reports validated")

if __name__ == "__main__":
    main()
