import json
import sys
from pathlib import Path

# Injection sys.path pour portabilité absolue V1.81.5
root_path = Path(__file__).resolve().parents[1]
src_path = str(root_path / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

VERSION = "V1.81.5"

def validate_v1_81_5_reports():
    report_path = root_path / f"reports/research/microstructure_data_contract_approval_intake_corrective_summary_{VERSION}.json"
    
    if not report_path.exists():
        print(f"ERROR: Report not found at {report_path}")
        sys.exit(1)
        
    with open(report_path) as f:
        data = json.load(f)
        
    checks = {
        "version": data.get("version") == VERSION,
        "test_quality_passed": data.get("test_quality_passed") is True,
        "placeholder_tests_count": data.get("placeholder_tests_count") == 0,
        "pass_only_tests_count": data.get("pass_only_tests_count") == 0,
        "scripts_portable": data.get("scripts_portable_without_manual_pythonpath") is True,
        "negative_coverage_complete": data.get("negative_test_coverage_complete") is True,
        "current_state_consistent": data.get("current_state_consistent") is True,
        "cross_file_alignment_passed": data.get("cross_file_alignment_passed") is True
    }
    
    all_passed = all(checks.values())
    
    print(f"--- Galapagos {VERSION} Report Validation ---")
    for k, v in checks.items():
        print(f"{k}: {'PASSED' if v else 'FAILED'}")
        
    if not all_passed:
        print("CRITICAL: Validation failed!")
        sys.exit(1)
        
    print("Certification V1.81.5 successful!")

if __name__ == "__main__":
    if "--help" in sys.argv:
        print(f"Galapagos {VERSION} Validator")
        sys.exit(0)
    validate_v1_81_5_reports()
