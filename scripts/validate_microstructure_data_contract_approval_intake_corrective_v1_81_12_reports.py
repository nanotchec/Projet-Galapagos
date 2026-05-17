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
    parser.add_argument("--version", default="v1_81_12")
    args = parser.parse_args()
    
    v_disp = "V1.81.12"
    v_norm = "v1_81_12"
    
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
            # zip_audit/smoke are optional if we are running the validator BEFORE they are generated
            if key in ["zip_audit", "zip_smoke"]:
                continue
            errors.append(f"Missing report: {path}")
        else:
            with open(path) as f:
                loaded_data[key] = json.load(f)

    if errors:
        print(f"ERROR: Validation {v_disp} failed (existence):\n" + "\n".join(f"  - {e}" for e in errors))
        sys.exit(1)

    # 1. Version Cross-Check
    for key in reports_to_check.keys():
        if key in loaded_data:
            val = loaded_data[key].get("version")
            if val != v_disp:
                errors.append(f"{key} version mismatch: {val} != {v_disp}")

    # 2. Pytest Alignment & Integrity
    counts = {}
    for key in ["pytest_audit", "summary", "metrics", "project_state"]:
        if key in loaded_data:
            c = loaded_data[key].get("pytest_test_count_observed")
            counts[key] = c
            if loaded_data[key].get("pytest_exit_code") != 0:
                errors.append(f"{key} reports pytest failure (exit code != 0)")
            if loaded_data[key].get("pytest_failed_count", 0) != 0:
                errors.append(f"{key} reports failed tests")
            if loaded_data[key].get("unmapped_tests") != []:
                errors.append(f"{key} contains unmapped tests")
            if loaded_data[key].get("weak_tests_count", 0) != 0:
                errors.append(f"{key} contains weak tests")
            
    if counts and len(set(counts.values())) > 1:
        errors.append(f"Pytest count divergence: {counts}")
    if counts and list(counts.values())[0] != 133: # Mis à jour à 133
         errors.append(f"Pytest count mismatch: {list(counts.values())[0]} != 133")

    # 3. Smoke Test Deep Validation
    if "zip_smoke" in loaded_data:
        smoke = loaded_data["zip_smoke"]
        if not smoke.get("smoke_test_passed"):
            errors.append("zip_smoke: smoke_test_passed != true")
        if smoke.get("smoke_commands_count", 0) < 3:
            errors.append(f"zip_smoke: smoke_commands_count ({smoke.get('smoke_commands_count')}) < 3")
        if smoke.get("smoke_passed_count") != smoke.get("smoke_commands_count"):
            errors.append("zip_smoke: smoke_passed_count != smoke_commands_count")
        if smoke.get("smoke_failed_count", 0) != 0:
            errors.append("zip_smoke: smoke_failed_count != 0")
        if not smoke.get("smoke_commands_not_empty"):
            errors.append("zip_smoke: smoke_commands_not_empty != true")
        if not smoke.get("commands"):
            errors.append("zip_smoke: commands list is empty")
        if smoke.get("smoke_timeout_detected") is not False:
            errors.append("zip_smoke: smoke_timeout_detected != false")
        if smoke.get("smoke_runs_audit_clean_zip_full_scan") is not False:
            errors.append("zip_smoke: smoke_runs_audit_clean_zip_full_scan != false")
        if smoke.get("smoke_runs_full_v1_81_12_pytest_suite") is not False:
            errors.append("zip_smoke: smoke_runs_full_v1_81_12_pytest_suite != false")
        if smoke.get("smoke_calls_smoke_script") is not False:
            errors.append("zip_smoke: smoke_calls_smoke_script != false")

    # Propagation check (only if smoke is loaded)
    if "zip_smoke" in loaded_data:
        smoke = loaded_data["zip_smoke"]
        for key in ["summary", "metrics", "project_state"]:
            if key in loaded_data:
                if loaded_data[key].get("smoke_test_passed") is not True:
                    errors.append(f"{key}: smoke_test_passed != true")
                if loaded_data[key].get("smoke_passed_count") != smoke.get("smoke_passed_count"):
                    errors.append(f"{key}: smoke_passed_count mismatch")

    # 4. Audit Deep Validation
    if "zip_audit" in loaded_data:
        audit = loaded_data["zip_audit"]
        if not audit.get("clean_zip_ready_for_external_review"):
            errors.append("zip_audit: clean_zip_ready_for_external_review != true")
        if audit.get("audit_zip_project_state_version") != v_disp:
            errors.append(f"zip_audit: audit_zip_project_state_version ({audit.get('audit_zip_project_state_version')}) != {v_disp}")
        if audit.get("audit_zip_version_parse_correct") is not True:
            errors.append("zip_audit: audit_zip_version_parse_correct != true")

    # 5. Safety Invariants
    for key in ["summary", "metrics", "project_state"]:
        if key in loaded_data:
            if loaded_data[key].get("network_executed") is not False:
                errors.append(f"{key}: network_executed is True (SAFETY VIOLATION)")
            if loaded_data[key].get("trading_allowed") is not False:
                errors.append(f"{key}: trading_allowed is True (SAFETY VIOLATION)")
            if loaded_data[key].get("v1_82_execution_attempted") is not False:
                errors.append(f"{key}: v1_82_execution_attempted is True (VERSION VIOLATION)")

    if errors:
        print(f"ERROR: Validation {v_disp} failed ({len(errors)}):\n" + "\n".join(f"  - {e}" for e in errors))
        sys.exit(1)

    print(f"SUCCESS: {v_disp} VALIDATED (Cross-file alignment OK).")

if __name__ == "__main__":
    main()
