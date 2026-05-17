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

    summary_p = reports_dir / f"microstructure_tiny_network_approval_summary_{v_norm}.json"
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
        "human_approval_gate_ready", "technical_pre_network_checklist_ready",
        "tiny_network_collection_preflight_authorization_ready",
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
    if summary.get("human_approval_gate_ready"):
        if summary.get("final_verdict") != "MICROSTRUCTURE_TINY_NETWORK_PREFLIGHT_APPROVAL_GATE_READY":
            print("ERROR: Wrong final_verdict for ready gate")
            sys.exit(1)
        if summary.get("next_allowed_phase") != "await_explicit_human_approval_for_tiny_network_preflight":
            print("ERROR: Wrong next_allowed_phase for ready gate")
            sys.exit(1)
        if "wait for explicit human approval phrase" not in summary.get("recommended_next_step", ""):
            print("ERROR: Missing approval phrase mention in recommendation")
            sys.exit(1)

    # Required fields
    if summary.get("verdict_alignment_status") != "TINY_NETWORK_APPROVAL_VERDICT_ALIGNED":
        print("ERROR: verdict_alignment_status incorrect")
        sys.exit(1)
    if summary.get("human_approval_required_before_network") is not True:
        print("ERROR: human_approval_required_before_network must be True")
        sys.exit(1)
    if summary.get("explicit_approval_phrase_required") is not True:
        print("ERROR: explicit_approval_phrase_required must be True")
        sys.exit(1)
    if not summary.get("required_approval_phrase"):
        print("ERROR: required_approval_phrase missing")
        sys.exit(1)
    if summary.get("max_request_count") != 1:
        print("ERROR: max_request_count must be 1")
        sys.exit(1)

    # Required files check
    required_stems = [
        "microstructure_tiny_network_approval_input_guard",
        "microstructure_v1_67_protocol_review",
        "microstructure_human_approval_gate",
        "microstructure_technical_pre_network_checklist",
        "microstructure_tiny_preflight_authorization_plan",
        "microstructure_go_no_go_policy",
        "microstructure_final_stop_conditions",
        "microstructure_rollback_cleanup_final_plan",
        "microstructure_audit_logging_plan",
        "microstructure_tiny_network_approval_decision",
        "microstructure_tiny_network_approval_recommendation",
        "microstructure_tiny_network_approval_summary",
        "microstructure_tiny_network_approval_consistency_check"
    ]
    for stem in required_stems:
        if not (reports_dir / f"{stem}_{v_norm}.json").exists():
            print(f"ERROR: Missing report {stem}_{v_norm}.json")
            sys.exit(1)
        if not (reports_dir / f"{stem}_{v_norm}.md").exists():
            print(f"ERROR: Missing report {stem}_{v_norm}.md")
            sys.exit(1)

    print(f"SUCCESS: V1.68 reports validated for {args.version}")

if __name__ == "__main__":
    main()
