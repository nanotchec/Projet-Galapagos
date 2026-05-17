import json
import sys
from pathlib import Path

def main():
    version_arg = "V1.81"
    if len(sys.argv) > 2 and sys.argv[1] == "--version":
        version_arg = sys.argv[2].upper()

    v_norm = version_arg.replace(".", "_").lower()
    root = Path.cwd()
    summary_p = root / f"reports/research/microstructure_data_contract_approval_intake_summary_{v_norm}.json"

    if not summary_p.exists():
        print(f"ERROR: Summary not found at {summary_p}")
        sys.exit(1)

    with open(summary_p) as f:
        summary = json.load(f)
    
    # 0. Version checks
    if summary.get("version") != "V1.81":
        print(f"ERROR: Expected version V1.81, got {summary.get('version')}")
        sys.exit(1)

    # 1. Load V1.80 context checks
    if summary.get("v1_80_review_loaded") is not True:
        print("ERROR: V1.80 review not loaded")
        sys.exit(1)
    if summary.get("v1_80_final_verdict") != "V1_79_REVIEW_PASSED_DATA_CONTRACT_DRYRUN_GATE_READY":
        print(f"ERROR: Unexpected V1.80 verdict: {summary.get('v1_80_final_verdict')}")
        sys.exit(1)

    # 2. Safety Invariants (NO NETWORK, NO DATA WRITE)
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
    if summary.get("parquet_created") is not False or summary.get("csv_created") is not False:
        print("ERROR: Data files created")
        sys.exit(1)
    if summary.get("dataset_created") is not False:
        print("ERROR: dataset_created must be false")
        sys.exit(1)
    if summary.get("data_write_approved") is not False:
        print("ERROR: data_write_approved must be false")
        sys.exit(1)
    if summary.get("dataset_materialization_approved") is not False:
        print("ERROR: dataset_materialization_approved must be false")
        sys.exit(1)
    if summary.get("trading_allowed") is not False:
        print("ERROR: trading_allowed must be false")
        sys.exit(1)
    if summary.get("real_orders_possible") is not False:
        print("ERROR: real_orders_possible must be false")
        sys.exit(1)

    # 3. Approval Consistency
    phrase_match = summary.get("approval_phrase_match")
    expected_phrase = "J'approuve V1.82 dry-run data contract reports-only, sans écriture data, sans dataset, sans trading."
    
    if phrase_match:
        if summary.get("approval_phrase_provided") != expected_phrase:
            print("ERROR: phrase_match=true but phrase provided is incorrect")
            sys.exit(1)
        if summary.get("human_approval_granted") is not True:
            print("ERROR: phrase_match=true but human_approval_granted=false")
            sys.exit(1)
        if summary.get("v1_82_authorized") is not True:
            print("ERROR: phrase_match=true but v1_82_authorized=false")
            sys.exit(1)
    else:
        if summary.get("human_approval_granted") is not False:
            print("ERROR: phrase_match=false but human_approval_granted=true")
            sys.exit(1)
        if summary.get("v1_82_authorized") is not False:
            print("ERROR: phrase_match=false but v1_82_authorized=true")
            sys.exit(1)

    print(f"SUCCESS: {version_arg} reports validated")

if __name__ == "__main__":
    main()
