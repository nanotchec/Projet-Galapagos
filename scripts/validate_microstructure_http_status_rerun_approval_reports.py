import json
import sys
from pathlib import Path

def main():
    version_arg = "V1.78"
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
    if summary.get("version") != "V1.78":
        print(f"ERROR: Expected version V1.78, got {summary.get('version')}")
        sys.exit(1)
    if summary.get("previous_base") != "V1.77.1":
        print(f"ERROR: Expected previous_base V1.77.1, got {summary.get('previous_base')}")
        sys.exit(1)

    # 1. Activity constraints (Must be 0 network)
    if summary.get("requests_executed_count") != 0:
        print("ERROR: requests_executed_count must be 0")
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
    if summary.get("no_new_network_request") is not True:
        print("ERROR: no_new_network_request must be true")
        sys.exit(1)

    # 2. Hardening Checks
    if summary.get("http_status_capture_hardened") is not True:
        print("ERROR: http_status_capture_hardened must be true")
        sys.exit(1)
    if summary.get("response_status_required_per_request") is not True:
        print("ERROR: response_status_required_per_request must be true")
        sys.exit(1)
    if summary.get("missing_status_codes_now_blocking") is not True:
        print("ERROR: missing_status_codes_now_blocking must be true")
        sys.exit(1)
    if summary.get("successful_response_requires_status_code") is not True:
        print("ERROR: successful_response_requires_status_code must be true")
        sys.exit(1)
    if summary.get("passed_verdict_requires_all_status_codes_present") is not True:
        print("ERROR: passed_verdict_requires_all_status_codes_present must be true")
        sys.exit(1)
    if summary.get("per_request_status_schema_defined") is not True:
        print("ERROR: per_request_status_schema_defined must be true")
        sys.exit(1)
    if summary.get("bounded_validator_hardened") is not True:
        print("ERROR: bounded_validator_hardened must be true")
        sys.exit(1)

    # 3. Approval Checks
    if summary.get("approval_phrase_validated") is not True:
        print("ERROR: approval_phrase_validated must be true")
        sys.exit(1)
    if summary.get("human_approval_granted") is not True:
        print("ERROR: human_approval_granted must be true")
        sys.exit(1)
    if summary.get("v1_79_http_status_rerun_authorized") is not True:
        print("ERROR: v1_79_http_status_rerun_authorized must be true")
        sys.exit(1)

    # 4. Limits & Security
    if summary.get("max_request_count") != 10:
        print("ERROR: max_request_count must be 10")
        sys.exit(1)
    if summary.get("max_records_preview_total") != 100:
        print("ERROR: max_records_preview_total must be 100")
        sys.exit(1)
    if summary.get("data_directory_writes_allowed") is not False:
        print("ERROR: data_directory_writes_allowed must be false")
        sys.exit(1)
    if summary.get("no_data_directory_writes") is not True:
        print("ERROR: no_data_directory_writes must be true")
        sys.exit(1)
    if summary.get("dataset_created") is not False:
        print("ERROR: dataset_created must be false")
        sys.exit(1)
    if summary.get("bounded_mini_collection_executed") is not False:
        print("ERROR: bounded_mini_collection_executed must be false")
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

    print(f"SUCCESS: {version_arg} reports validated")

if __name__ == "__main__":
    main()
