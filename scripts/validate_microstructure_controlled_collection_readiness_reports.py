import argparse
import json
from pathlib import Path
import sys

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    v_norm = args.version.replace(".", "_").lower()
    root = Path(__file__).parent.parent
    reports_dir = root / "reports/research"

    summary_p = reports_dir / f"microstructure_controlled_collection_summary_{v_norm}.json"
    state_p = root / "reports/PROJECT_STATE.json"
    metrics_p = root / "reports/current/latest_metrics.json"
    rec_p = reports_dir / f"{v_norm}_recommendation.json"

    files = [summary_p, state_p, metrics_p, rec_p]
    data = []
    for f in files:
        if not f.exists():
            print(f"ERROR: Missing file {f}")
            sys.exit(1)
        with open(f) as j:
            data.append(json.load(j))

    summary, state, metrics, rec = data

    # Cross-validation
    fields = [
        "final_verdict", "recommended_next_step", "next_allowed_phase",
        "controlled_collection_readiness_review_passed", "tiny_collection_protocol_defined",
        "human_approval_granted"
    ]

    for field in fields:
        val = summary.get(field)
        if state.get(field) != val or metrics.get(field) != val or rec.get(field) != val:
            print(f"ERROR: Field mismatch for '{field}'")
            print(f"Summary: {summary.get(field)}")
            print(f"State: {state.get(field)}")
            print(f"Metrics: {metrics.get(field)}")
            print(f"Rec: {rec.get(field)}")
            sys.exit(1)

    # Safety checks
    if summary.get("human_approval_granted") is not False:
        print("ERROR: human_approval_granted must be False")
        sys.exit(1)
    if summary.get("network_enabled") is not False:
        print("ERROR: network_enabled must be False")
        sys.exit(1)
    if summary.get("requests_executed_count", 0) != 0:
        print("ERROR: requests_executed_count must be 0")
        sys.exit(1)
    if summary.get("no_data_directory_writes") is not True:
        print("ERROR: no_data_directory_writes must be True")
        sys.exit(1)

    # Verdict alignment
    if summary.get("controlled_collection_readiness_review_passed"):
        if summary.get("final_verdict") != "MICROSTRUCTURE_CONTROLLED_COLLECTION_READINESS_REVIEW_PASSED":
            print("ERROR: Wrong final_verdict for passed review")
            sys.exit(1)
        if summary.get("next_allowed_phase") != "human_approval_required_for_tiny_network_collection_preflight":
            print("ERROR: Wrong next_allowed_phase for passed review")
            sys.exit(1)
        if "obtain explicit human approval" not in summary.get("recommended_next_step", ""):
            print("ERROR: Missing human approval mention in recommendation")
            sys.exit(1)

    # Required files check
    required_stems = [
        "microstructure_controlled_collection_input_guard",
        "microstructure_controlled_collection_readiness_review",
        "microstructure_network_activation_risk_audit",
        "microstructure_tiny_collection_protocol",
        "microstructure_human_approval_protocol",
        "microstructure_collection_boundary_policy",
        "microstructure_stop_conditions_policy",
        "microstructure_rollback_cleanup_plan",
        "microstructure_data_write_policy",
        "microstructure_pre_execution_validation_plan",
        "microstructure_controlled_collection_decision",
        "microstructure_controlled_collection_recommendation",
        "microstructure_controlled_collection_summary",
        "microstructure_controlled_collection_consistency_check"
    ]
    for stem in required_stems:
        if not (reports_dir / f"{stem}_{v_norm}.json").exists():
            print(f"ERROR: Missing report {stem}_{v_norm}.json")
            sys.exit(1)
        if not (reports_dir / f"{stem}_{v_norm}.md").exists():
            print(f"ERROR: Missing report {stem}_{v_norm}.md")
            sys.exit(1)

    print(f"SUCCESS: V1.67 reports validated for {args.version}")

if __name__ == "__main__":
    main()
