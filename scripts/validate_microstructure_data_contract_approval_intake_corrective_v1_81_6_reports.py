import argparse
import json
import sys
from pathlib import Path

# Injection sys.path
root_path = Path(__file__).resolve().parents[1]
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from galapagos.research.microstructure_data_contract_approval_intake.current_state_alignment import version_to_suffix, parse_version

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="V1.81.6")
    args = parser.parse_args()

    v_disp = parse_version(args.version)
    v_suffix = version_to_suffix(args.version)
    
    reports_dir = Path("reports")
    
    required_reports = [
        f"negative_test_coverage_{v_suffix}.json",
        f"test_quality_{v_suffix}.json",
        f"portability_audit_{v_suffix}.json",
        f"metadata_audit_{v_suffix}.json",
        f"report_index_audit_{v_suffix}.json",
        f"current_state_alignment_{v_suffix}.json"
    ]

    missing = []
    for r in required_reports:
        if not (reports_dir / r).exists():
            missing.append(r)
    
    if missing:
        print(f"ERROR: Missing reports for {v_disp}: {missing}")
        sys.exit(1)

    # Validate alignment
    with open(reports_dir / f"current_state_alignment_{v_suffix}.json") as f:
        data = json.load(f)
    
    if data.get("version") != v_disp:
        print(f"ERROR: Version mismatch in report (expected {v_disp}, got {data.get('version')})")
        sys.exit(1)
        
    expected_verdict = f"{v_suffix.upper()}_RELEASE_PACKAGING_AND_SMOKE_HARDENING_PASSED"
    if data.get("final_verdict") != expected_verdict:
        print(f"ERROR: Verdict mismatch (expected {expected_verdict}, got {data.get('final_verdict')})")
        sys.exit(1)

    if not data.get("test_quality_passed"):
        print("ERROR: Test quality audit failed")
        sys.exit(1)

    print(f"SUCCESS: All V1.81.6 reports validated for {v_disp}")

if __name__ == "__main__":
    main()
