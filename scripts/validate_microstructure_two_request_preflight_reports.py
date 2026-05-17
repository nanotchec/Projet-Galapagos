import json
import sys
from pathlib import Path

def main():
    version_arg = "V1.74"
    if len(sys.argv) > 2 and sys.argv[1] == "--version":
        version_arg = sys.argv[2].upper()

    v_norm = version_arg.replace(".", "_").lower()
    root = Path.cwd()
    summary_p = root / f"reports/research/microstructure_two_request_preflight_summary_{v_norm}.json"

    if not summary_p.exists():
        print(f"ERROR: Summary not found at {summary_p}")
        sys.exit(1)

    with open(summary_p) as f:
        summary = json.load(f)
    
    # 0. Version checks
    if summary.get("version") != "V1.74":
        print(f"ERROR: Expected version V1.74, got {summary.get('version')}")
        sys.exit(1)
    if summary.get("previous_base") != "V1.73.1":
        print(f"ERROR: Expected previous_base V1.73.1, got {summary.get('previous_base')}")
        sys.exit(1)

    # 1. Activity constraints
    if summary.get("requests_executed_count") > 2:
        print(f"ERROR: requests_executed_count {summary.get('requests_executed_count')} > 2")
        sys.exit(1)
    
    if summary.get("max_request_count") != 2:
        print("ERROR: max_request_count must be 2")
        sys.exit(1)

    if summary.get("request_retry_count") != 0:
        print("ERROR: request_retry_count must be 0")
        sys.exit(1)

    if summary.get("pagination_used") is not False:
        print("ERROR: pagination_used must be false")
        sys.exit(1)

    # 2. Authorization & Secrets
    if summary.get("authenticated_request_allowed") is not False:
        print("ERROR: authenticated_request_allowed must be false")
        sys.exit(1)

    if summary.get("secrets_used") is not False:
        print("ERROR: secrets_used must be false")
        sys.exit(1)

    # 3. Data writes
    if summary.get("data_directory_writes_allowed") is not False:
        print("ERROR: data_directory_writes_allowed must be false")
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

    # 4. Preview constraints
    if summary.get("records_preview_count_total", 0) > 20:
        print("ERROR: records_preview_count_total > 20")
        sys.exit(1)

    if summary.get("records_preview_count_per_request_lte_10") is not True:
        print("ERROR: records_preview_count_per_request_lte_10 must be true")
        sys.exit(1)

    # 5. Trading & Strategy
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

    # 6. Machine specific paths
    if summary.get("machine_specific_paths_found"):
        print("ERROR: Machine specific paths found")
        sys.exit(1)

    print(f"SUCCESS: V1.74 reports validated for {version_arg}")

if __name__ == "__main__":
    main()
