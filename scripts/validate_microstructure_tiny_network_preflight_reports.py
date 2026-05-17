import argparse
import json
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v1.71")
    args = parser.parse_args()

    v_norm = args.version.replace(".", "_").lower()
    reports_dir = Path("reports/research")
    summary_p = reports_dir / f"microstructure_tiny_network_summary_{v_norm}.json"

    if not summary_p.exists():
        print(f"ERROR: Summary report {summary_p} not found")
        sys.exit(1)

    with open(summary_p) as f:
        summary = json.load(f)
    
    # 0. Version checks
    if summary.get("version") != "V1.71":
        print(f"ERROR: Expected version V1.71, got {summary.get('version')}")
        sys.exit(1)
    if summary.get("previous_base") != "V1.70.2":
        print(f"ERROR: Expected previous_base V1.70.2, got {summary.get('previous_base')}")
        sys.exit(1)

    # 1. Network constraints
    if summary.get("requests_executed_count", 0) > 1:
        print(f"ERROR: Too many requests executed: {summary.get('requests_executed_count')}")
        sys.exit(1)
    if summary.get("max_request_count") != 1:
        print("ERROR: max_request_count must be 1")
        sys.exit(1)
    if summary.get("request_retry_count") != 0:
        print("ERROR: request_retry_count must be 0")
        sys.exit(1)
    if summary.get("pagination_used") is True:
        print("ERROR: pagination_used must be False")
        sys.exit(1)

    # 2. Safety constraints
    if summary.get("authenticated_request_allowed") is True:
        print("ERROR: authenticated_request_allowed must be False")
        sys.exit(1)
    if summary.get("secrets_used") is True:
        print("ERROR: secrets_used must be False")
        sys.exit(1)
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

    # 3. Artifact checks
    if summary.get("records_preview_count", 0) > 10:
        print(f"ERROR: Too many records in preview: {summary.get('records_preview_count')}")
        sys.exit(1)

    required_stems = [
        "microstructure_tiny_network_input_guard",
        "microstructure_tiny_network_endpoint_policy",
        "microstructure_one_request_guard",
        "microstructure_tiny_network_client",
        "microstructure_response_preview",
        "microstructure_no_data_write_guard",
        "microstructure_tiny_network_safety_audit",
        "microstructure_tiny_network_decision",
        "microstructure_tiny_network_recommendation",
        "microstructure_tiny_network_summary",
        "microstructure_tiny_network_consistency_check",
        "v1_71_recommendation"
    ]
    for stem in required_stems:
        if stem == "v1_71_recommendation":
            json_p = reports_dir / f"{stem}.json"
        else:
            json_p = reports_dir / f"{stem}_{v_norm}.json"

        if not json_p.exists():
            print(f"ERROR: Missing report {json_p.name}")
            sys.exit(1)

    print(f"SUCCESS: V1.71 reports validated for {args.version}")

if __name__ == "__main__":
    main()
