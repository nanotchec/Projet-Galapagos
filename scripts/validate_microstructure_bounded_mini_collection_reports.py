import json
import sys
from pathlib import Path

def main():
    version_arg = "V1.77"
    if len(sys.argv) > 2 and sys.argv[1] == "--version":
        version_arg = sys.argv[2].upper()

    v_norm = version_arg.replace(".", "_").lower()
    root = Path.cwd()
    summary_p = root / f"reports/research/microstructure_bounded_mini_collection_summary_{v_norm}.json"

    if not summary_p.exists():
        print(f"ERROR: Summary not found at {summary_p}")
        sys.exit(1)

    with open(summary_p) as f:
        summary = json.load(f)
    
    # 0. Version checks
    if summary.get("version") != "V1.77":
        print(f"ERROR: Expected version V1.77, got {summary.get('version')}")
        sys.exit(1)
    if summary.get("previous_base") != "V1.76.1":
        print(f"ERROR: Expected previous_base V1.76.1, got {summary.get('previous_base')}")
        sys.exit(1)

    # 1. Activity constraints
    req_count = summary.get("requests_executed_count")
    if req_count > 10:
        print(f"ERROR: requests_executed_count {req_count} > 10")
        sys.exit(1)
    
    # NEW: Status code hardening
    success_count = summary.get("successful_response_count", 0)
    status_codes = summary.get("response_status_codes", [])
    if success_count > 0:
        if not status_codes or None in status_codes:
            # We allow it ONLY if version is NOT V1.77.1 (V1.77 was buggy)
            # but we print a warning. Actually for the hardening we want to REJECT it
            # unless it's explicitly marked as incomplete (which V1.77 wasn't).
            # The user says "durcir le validateur pour refuser response_status_codes = [None] quand successful_response_count > 0"
            print(f"ERROR: response_status_codes contains None while success_count={success_count}")
            sys.exit(1)
    
    if summary.get("max_request_count") != 10:
        print(f"ERROR: max_request_count {summary.get('max_request_count')} != 10")
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

    if summary.get("dataset_creation_allowed") is not False:
        print("ERROR: dataset_creation_allowed must be false")
        sys.exit(1)

    if summary.get("new_data_files_created") is not False:
        print("ERROR: new_data_files_created must be false")
        sys.exit(1)

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

    if summary.get("research_dataset_updated") is not False:
        print("ERROR: research_dataset_updated must be false")
        sys.exit(1)

    # 3. Preview limits
    preview_total = summary.get("records_preview_count_total")
    if preview_total > 100:
        print(f"ERROR: records_preview_count_total {preview_total} > 100")
        sys.exit(1)

    if summary.get("records_preview_count_per_request_lte_10") is not True:
        print("ERROR: records_preview_count_per_request_lte_10 must be true")
        sys.exit(1)

    # 4. Strategy & Trading
    if summary.get("strategy_link_allowed") is not False:
        print("ERROR: strategy_link_allowed must be false")
        sys.exit(1)

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

    # 5. Machine specific paths
    if summary.get("machine_specific_paths_found"):
        print("ERROR: Machine specific paths found")
        sys.exit(1)

    print(f"SUCCESS: {version_arg} reports validated")

if __name__ == "__main__":
    main()
