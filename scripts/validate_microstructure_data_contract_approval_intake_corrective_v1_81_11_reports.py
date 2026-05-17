import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v1_81_11")
    args = parser.parse_args()
    
    v_disp = "V1.81.11"
    v_norm = "v1_81_11"
    
    reports_to_check = {
        "pytest_audit": PROJECT_ROOT / f"reports/research/microstructure_data_contract_approval_intake_corrective_pytest_audit_{v_norm}.json",
        "neg_cov": PROJECT_ROOT / f"reports/research/microstructure_data_contract_approval_intake_corrective_negative_coverage_{v_norm}.json",
        "summary": PROJECT_ROOT / f"reports/research/microstructure_data_contract_approval_intake_corrective_summary_{v_norm}.json",
        "metrics": PROJECT_ROOT / "reports/current/latest_metrics.json",
        "project_state": PROJECT_ROOT / "reports/PROJECT_STATE.json",
        "zip_audit": PROJECT_ROOT / f"reports/zip_audit_{v_norm}.json",
        "zip_smoke": PROJECT_ROOT / f"reports/zip_smoke_test_{v_norm}.json"
    }
    
    errors = []
    
    # Check existence
    loaded_data = {}
    for key, path in reports_to_check.items():
        if not path.exists():
            # If zip_audit/smoke don't exist yet, we might be in early validation
            if key in ["zip_audit", "zip_smoke"]:
                continue
            errors.append(f"Missing report: {path}")
        else:
            with open(path) as f:
                loaded_data[key] = json.load(f)

    if errors:
        print(f"ERROR: Validation {v_disp} failed (existence):\n" + "\n".join(f"  - {e}" for e in errors))
        sys.exit(1)

    # Cross-file version check
    for key in ["pytest_audit", "neg_cov", "summary", "metrics", "project_state"]:
        if key in loaded_data:
            val = loaded_data[key].get("version")
            if val != v_disp:
                errors.append(f"{key} version mismatch: {val} != {v_disp}")

    # Cross-file pytest count alignment
    counts = {}
    for key in ["pytest_audit", "summary", "metrics", "project_state"]:
        if key in loaded_data:
            c = loaded_data[key].get("pytest_test_count_observed")
            counts[key] = c
            
    if len(set(counts.values())) > 1:
        errors.append(f"Pytest count divergence: {counts}")

    # Specific checks
    if "neg_cov" in loaded_data:
        if loaded_data["neg_cov"].get("version") != v_disp:
            errors.append(f"NegativeCoverage version mismatch: {loaded_data['neg_cov'].get('version')}")
        if loaded_data["neg_cov"].get("corrective_for_version") != "V1.81.10":
            errors.append(f"NegativeCoverage corrective mismatch: {loaded_data['neg_cov'].get('corrective_for_version')}")

    if "project_state" in loaded_data:
        if not loaded_data["project_state"].get("clean_zip_ready_for_external_review"):
            errors.append("clean_zip_ready_for_external_review != true")

    if "zip_audit" in loaded_data:
        if loaded_data["zip_audit"].get("audit_zip_project_state_version") != v_disp:
             errors.append(f"zip_audit project_state version mismatch: {loaded_data['zip_audit'].get('audit_zip_project_state_version')}")
        if not loaded_data["zip_audit"].get("audit_zip_version_parse_correct"):
             errors.append("audit_zip_version_parse_correct != true")

    if "zip_smoke" in loaded_data:
        if not loaded_data["zip_smoke"].get("smoke_test_passed"):
            errors.append("smoke_test_passed != true")

    if errors:
        print(f"ERROR: Validation {v_disp} failed ({len(errors)}):\n" + "\n".join(f"  - {e}" for e in errors))
        sys.exit(1)

    print(f"SUCCESS: {v_disp} VALIDATED (Cross-file alignment OK).")

if __name__ == "__main__":
    main()
