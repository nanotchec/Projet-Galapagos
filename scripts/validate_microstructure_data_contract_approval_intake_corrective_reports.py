import json
import sys
from pathlib import Path

def main():
    version_arg = "V1.81.1"
    if len(sys.argv) > 2 and sys.argv[1] == "--version":
        version_arg = sys.argv[2].upper()

    v_norm = version_arg.replace(".", "_").lower()
    root = Path.cwd()
    summary_p = root / f"reports/research/microstructure_data_contract_approval_intake_corrective_summary_{v_norm}.json"

    if not summary_p.exists():
        print(f"ERROR: Summary not found at {summary_p}")
        sys.exit(1)

    with open(summary_p) as f:
        summary = json.load(f)
    
    # 0. Version checks
    if summary.get("version") != "V1.81.1":
        print(f"ERROR: Expected version V1.81.1, got {summary.get('version')}")
        sys.exit(1)
    if summary.get("corrective_for_version") != "V1.81":
        print(f"ERROR: corrective_for_version must be V1.81")
        sys.exit(1)
    if summary.get("final_verdict") != "V1_81_1_CORRECTIVE_APPROVAL_INTAKE_HARDENING_PASSED":
        print(f"ERROR: Unexpected verdict: {summary.get('final_verdict')}")
        sys.exit(1)

    # 1. Scope Drift checks
    if summary.get("scope_drift_detected") is not False:
        print("ERROR: scope_drift_detected must be false")
        sys.exit(1)
    if summary.get("v1_82_execution_attempted") is not False:
        print("ERROR: v1_82_execution_attempted must be false")
        sys.exit(1)
    if summary.get("data_contract_dryrun_executed") is not False:
        print("ERROR: data_contract_dryrun_executed must be false")
        sys.exit(1)

    # 2. Coverage checks
    if summary.get("negative_test_coverage_complete") is not True:
        print("ERROR: negative_test_coverage_complete must be true")
        sys.exit(1)
    if summary.get("missing_negative_invariants"):
        print("ERROR: missing_negative_invariants must be empty")
        sys.exit(1)
    if summary.get("required_negative_invariants_count") != summary.get("covered_negative_invariants_count"):
        print("ERROR: Invariant count mismatch")
        sys.exit(1)
    if (summary.get("required_negative_invariants_count") or 0) < 33:
        print("ERROR: required_negative_invariants_count must be at least 33")
        sys.exit(1)

    # 3. Approval Invariants
    if summary.get("approval_phrase_match") is not True:
        print("ERROR: approval_phrase_match must be true")
        sys.exit(1)
    if summary.get("human_approval_granted") is not True:
        print("ERROR: human_approval_granted must be true")
        sys.exit(1)
    if summary.get("v1_82_authorized") is not True:
        print("ERROR: v1_82_authorized must be true")
        sys.exit(1)
    if summary.get("authorized_future_version") != "V1.82":
        print("ERROR: authorized_future_version must be V1.82")
        sys.exit(1)

    # 4. Safety Invariants (Network, Data, Trading, ML)
    # Network
    if summary.get("network_executed") is not False:
        print("ERROR: network_executed must be false")
        sys.exit(1)
    if (summary.get("request_retry_count") or 0) > 0:
        print("ERROR: request_retry_count must be 0")
        sys.exit(1)
    # Data
    if summary.get("data_directory_writes_allowed") is not False:
        print("ERROR: data_directory_writes_allowed must be false")
        sys.exit(1)
    if summary.get("no_data_directory_writes") is not True:
        print("ERROR: no_data_directory_writes must be true")
        sys.exit(1)
    if summary.get("parquet_created") is not False or summary.get("csv_created") is not False:
        print("ERROR: Data files detected")
        sys.exit(1)
    if summary.get("dataset_created") is not False:
        print("ERROR: dataset_created must be false")
        sys.exit(1)
    # Trading / ML
    if summary.get("trading_allowed") is not False:
        print("ERROR: trading_allowed must be false")
        sys.exit(1)
    if summary.get("no_real_trading") is not True:
        print("ERROR: no_real_trading must be true")
        sys.exit(1)
    if summary.get("ml_signal_validation_executed") is not False:
        print("ERROR: ML activity detected")
        sys.exit(1)
    if summary.get("predictions_created") is not False:
        print("ERROR: predictions detected")
        sys.exit(1)

    print(f"SUCCESS: {version_arg} reports validated")

if __name__ == "__main__":
    main()
