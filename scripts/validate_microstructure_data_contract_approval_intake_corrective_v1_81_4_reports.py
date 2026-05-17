import json
import sys
from pathlib import Path
from src.galapagos.research.microstructure_data_contract_approval_intake.current_state_alignment import CRITICAL_CROSS_FILE_FIELDS

def main():
    version_arg = "V1.81.4"
    if len(sys.argv) > 2 and sys.argv[1] == "--version":
        version_arg = sys.argv[2].upper()

    v_norm = version_arg.replace(".", "_").lower()
    root = Path.cwd()
    summary_p = root / f"reports/research/microstructure_data_contract_approval_intake_corrective_summary_{v_norm}.json"
    metrics_p = root / "reports/current/latest_metrics.json"
    state_p = root / "reports/PROJECT_STATE.json"

    if not summary_p.exists():
        print(f"ERROR: Summary not found at {summary_p}")
        sys.exit(1)

    with open(summary_p) as f:
        summary = json.load(f)
    
    # 0. Core checks
    if summary.get("version") != "V1.81.4":
        print(f"ERROR: Expected version V1.81.4, got {summary.get('version')}")
        sys.exit(1)
    if summary.get("final_verdict") != "V1_81_4_STRICT_CURRENT_STATE_ALIGNMENT_PASSED":
        print(f"ERROR: Unexpected verdict: {summary.get('final_verdict')}")
        sys.exit(1)

    # 1. Cross-File Alignment Strict Validation
    if summary.get("cross_file_alignment_checked") is not True:
        print("ERROR: cross_file_alignment_checked must be true")
        sys.exit(1)
    if summary.get("cross_file_alignment_passed") is not True:
        print("ERROR: cross_file_alignment_passed must be true")
        sys.exit(1)
    if summary.get("cross_file_mismatch_count") != 0:
        print(f"ERROR: cross_file_mismatch_count is {summary.get('cross_file_mismatch_count')}")
        sys.exit(1)
    if summary.get("cross_file_mismatches") != []:
        print("ERROR: cross_file_mismatches must be empty")
        sys.exit(1)
    if summary.get("latest_metrics_matches_summary") is not True:
        print("ERROR: latest_metrics_matches_summary must be true")
        sys.exit(1)
    if summary.get("project_state_matches_summary") is not True:
        print("ERROR: project_state_matches_summary must be true")
        sys.exit(1)

    # 2. Strict Comparison of ALL critical fields in ALL 3 files
    if not metrics_p.exists() or not state_p.exists():
        print("ERROR: current state JSON files missing")
        sys.exit(1)

    with open(metrics_p) as f:
        metrics = json.load(f)
    with open(state_p) as f:
        state = json.load(f)

    for field in CRITICAL_CROSS_FILE_FIELDS:
        s_val = summary.get(field)
        m_val = metrics.get(field)
        p_val = state.get(field)

        if m_val != s_val:
            print(f"ERROR: Divergence in latest_metrics for {field}")
            sys.exit(1)
        if p_val != s_val:
            print(f"ERROR: Divergence in PROJECT_STATE for {field}")
            sys.exit(1)
        if m_val is None and field != "unmapped_tests": # Tolerance for empty list
             pass

    # 3. Consistency Flag Check
    if metrics.get("current_state_consistent") is not True:
        print("ERROR: latest_metrics.json has current_state_consistent=false")
        sys.exit(1)
    if state.get("current_state_consistent") is not True:
        print("ERROR: PROJECT_STATE.json has current_state_consistent=false")
        sys.exit(1)

    # 4. Report Index & Summary MD
    ls_p = root / "reports/current/latest_summary.md"
    with open(ls_p) as f:
        ls_content = f.read()
        if "# Latest Summary - Galapagos V1.81.4" not in ls_content:
            print("ERROR: latest_summary.md title mismatch")
            sys.exit(1)

    ri_p = root / "reports/REPORT_INDEX.md"
    with open(ri_p) as f:
        ri_content = f.read()
        if "V1.81.4" not in ri_content:
            print("ERROR: REPORT_INDEX.md missing V1.81.4")
            sys.exit(1)

    print(f"SUCCESS: {version_arg} reports validated (Strict cross-file alignment 47/47 fields)")

if __name__ == "__main__":
    main()
