import json
import sys
from pathlib import Path

def main():
    version_arg = "V1.81.2"
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
    
    # 0. Core checks
    if summary.get("version") != "V1.81.2":
        print(f"ERROR: Expected version V1.81.2, got {summary.get('version')}")
        sys.exit(1)
    if summary.get("corrective_for_version") != "V1.81.1":
        print(f"ERROR: corrective_for_version must be V1.81.1")
        sys.exit(1)
    if summary.get("final_verdict") != "V1_81_2_CORRECTIVE_APPROVAL_INTAKE_HARDENING_PASSED":
        print(f"ERROR: Unexpected verdict: {summary.get('final_verdict')}")
        sys.exit(1)

    # 1. Coverage Integrity
    if summary.get("negative_test_coverage_complete") is not True:
        print("ERROR: negative_test_coverage_complete must be true")
        sys.exit(1)
    if summary.get("missing_negative_invariants"):
        print("ERROR: missing_negative_invariants detected")
        sys.exit(1)
    if summary.get("duplicate_test_names"):
        print("ERROR: duplicate_test_names detected")
        sys.exit(1)
    if summary.get("required_negative_invariants_count") != 33:
        print("ERROR: required_negative_invariants_count must be 33")
        sys.exit(1)
    if summary.get("safety_guard_checked_invariants_count") != 33:
        print("ERROR: safety_guard_checked_invariants_count must be 33")
        sys.exit(1)
    if summary.get("validator_checked_invariants_count") != 33:
        print("ERROR: validator_checked_invariants_count must be 33")
        sys.exit(1)

    # 2. Individual Invariant Validation (33)
    invariants = [
        # Network
        ("network_executed", False),
        ("new_network_requests_executed", False),
        ("request_retry_count", 0),
        ("pagination_used", False),
        ("authenticated_request_allowed", False),
        ("secrets_used", False),
        # Data
        ("data_directory_writes_allowed", False),
        ("new_data_files_created", False),
        ("no_data_directory_writes", True),
        ("parquet_created", False),
        ("csv_created", False),
        ("sqlite_created", False),
        ("jsonl_created", False),
        ("db_created", False),
        ("dataset_created", False),
        ("research_dataset_updated", False),
        ("data_write_approved", False),
        ("dataset_materialization_approved", False),
        # Trading/ML
        ("strategy_link_allowed", False),
        ("trading_allowed", False),
        ("no_strategy_validated", True),
        ("no_paper_live", True),
        ("no_real_trading", True),
        ("real_orders_possible", False),
        ("holdout_executed", False),
        ("codex_cli_called", False),
        ("ml_signal_validation_executed", False),
        ("predictions_created", False),
        ("labels_created", False),
        ("targets_created", False),
        # Scope
        ("v1_82_execution_attempted", False),
        ("data_contract_dryrun_executed", False),
        ("scope_drift_detected", False)
    ]

    for field, expected in invariants:
        actual = summary.get(field)
        if actual != expected:
            print(f"ERROR: Invariant violation for {field}. Expected {expected}, got {actual}")
            sys.exit(1)

    # 3. Approval Invariants
    if summary.get("approval_phrase_match") is not True:
        print("ERROR: approval_phrase_match must be true")
        sys.exit(1)
    if summary.get("human_approval_granted") is not True:
        print("ERROR: human_approval_granted must be true")
        sys.exit(1)
    if summary.get("authorized_future_version") != "V1.82":
        print("ERROR: authorized_future_version must be V1.82")
        sys.exit(1)
    if summary.get("release_ready_for_external_review") is not True:
        print("ERROR: release_ready_for_external_review must be true")
        sys.exit(1)

    print(f"SUCCESS: {version_arg} reports validated (33/33 invariants checked)")

if __name__ == "__main__":
    main()
