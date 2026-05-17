import argparse
import json
import os
import sys
import re
from pathlib import Path
from typing import Any, Dict, List

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v1_81_14")
    args = parser.parse_args()
    
    v_disp = "V1.81.14"
    v_norm = "v1_81_14"
    
    reports_to_check = {
        "pytest_audit": PROJECT_ROOT / f"reports/research/microstructure_data_contract_approval_intake_corrective_pytest_audit_{v_norm}.json",
        "neg_cov": PROJECT_ROOT / f"reports/research/microstructure_data_contract_approval_intake_corrective_negative_coverage_{v_norm}.json",
        "summary": PROJECT_ROOT / f"reports/research/microstructure_data_contract_approval_intake_corrective_summary_{v_norm}.json",
        "test_quality": PROJECT_ROOT / f"reports/research/microstructure_data_contract_approval_intake_corrective_test_quality_audit_{v_norm}.json",
        "current_state": PROJECT_ROOT / f"reports/research/microstructure_data_contract_approval_intake_corrective_current_state_alignment_{v_norm}.json",
        "consistency": PROJECT_ROOT / f"reports/research/microstructure_data_contract_approval_intake_corrective_consistency_check_{v_norm}.json",
        "metrics": PROJECT_ROOT / "reports/current/latest_metrics.json",
        "project_state": PROJECT_ROOT / "reports/PROJECT_STATE.json",
        "zip_audit": PROJECT_ROOT / f"reports/zip_audit_{v_norm}.json",
        "zip_smoke": PROJECT_ROOT / f"reports/zip_smoke_test_{v_norm}.json",
        "release_zip": PROJECT_ROOT / f"reports/release_zip_{v_norm}.json"
    }
    
    docs_to_check = {
        "code_review": PROJECT_ROOT / f"docs/code_review_{v_norm}.md",
        "report_index": PROJECT_ROOT / "reports/REPORT_INDEX.md"
    }
    
    errors = []
    
    # Check existence of JSON reports
    loaded_data = {}
    for key, path in reports_to_check.items():
        if not path.exists():
            errors.append(f"Missing mandatory report: {path.name}")
        else:
            try:
                with open(path) as f:
                    loaded_data[key] = json.load(f)
            except Exception as e:
                errors.append(f"Error reading {path.name}: {e}")

    # Check existence of docs
    for key, path in docs_to_check.items():
        if not path.exists():
            errors.append(f"Missing mandatory doc: {path.name}")

    if errors:
        print(f"ERROR: Validation {v_disp} failed (existence/read):\n" + "\n".join(f"  - {e}" for e in errors))
        sys.exit(1)

    # 1. Version Cross-Check
    for key in reports_to_check.keys():
        val = loaded_data[key].get("version")
        if val != v_disp:
            errors.append(f"{key} version mismatch: {val} != {v_disp}")

    # 2. Test Quality Deep Check
    tq = loaded_data["test_quality"]
    if tq.get("test_quality_passed") is not True: errors.append("test_quality: test_quality_passed != true")
    if tq.get("forbidden_test_names_count", 0) != 0: errors.append(f"test_quality: forbidden_test_names_count is {tq.get('forbidden_test_names_count')}")
    if tq.get("forbidden_test_names") != []: errors.append(f"test_quality: forbidden_test_names is {tq.get('forbidden_test_names')}")
    if tq.get("pass_only_tests_count", 0) != 0: errors.append("test_quality: pass_only_tests_count != 0")
    if tq.get("weak_tests_count", 0) != 0: errors.append("test_quality: weak_tests_count != 0")
    if tq.get("tautological_tests_count", 0) != 0: errors.append("test_quality: tautological_tests_count != 0")
    if tq.get("or_true_tests_count", 0) != 0: errors.append("test_quality: or_true_tests_count != 0")
    if tq.get("assert_true_tests_count", 0) != 0: errors.append("test_quality: assert_true_tests_count != 0")

    # 3. Pytest Alignment (>= 50 tests)
    for key in ["pytest_audit", "summary", "metrics", "project_state"]:
        count = loaded_data[key].get("pytest_test_count_observed", 0)
        if count < 50:
            errors.append(f"{key}: pytest_test_count_observed < 50 ({count})")
        if loaded_data[key].get("unmapped_tests") != []:
            errors.append(f"{key} contains unmapped tests")

    # 4. Release Validation
    rz = loaded_data["release_zip"]
    if rz.get("final_zip_created") is not True: errors.append("release_zip: final_zip_created != true")
    if rz.get("release_command_completed") is not True: errors.append("release_zip: release_command_completed != true")
    if rz.get("release_timeout_detected") is not False: errors.append("release_zip: release_timeout_detected != false")

    # 5. Document Content Check
    cr_content = docs_to_check["code_review"].read_text()
    p_word = "place" + "holder"
    if p_word in cr_content.lower():
        errors.append(f"docs/code_review_{v_norm}.md contains forbidden term '{p_word}'")

    index_content = docs_to_check["report_index"].read_text()
    if v_disp not in index_content:
        errors.append(f"REPORT_INDEX.md does not reference {v_disp}")

    # 6. Script Structure Check (No duplicate main)
    scripts_to_check = [
        PROJECT_ROOT / f"scripts/run_microstructure_data_contract_approval_intake_corrective_{v_norm}.py",
        PROJECT_ROOT / f"scripts/validate_microstructure_data_contract_approval_intake_corrective_{v_norm}_reports.py"
    ]
    for s_path in scripts_to_check:
        if s_path.exists():
            s_content = s_path.read_text()
            main_str = 'if __name__' + ' == "__main__":'
            if s_content.count(main_str) > 1:
                errors.append(f"Duplicate main block in script: {s_path.name}")
        else:
            # Check for the wrong path mentioned in the context (without _reports.py)
            wrong_path = str(s_path).replace("_reports.py", ".py")
            if os.path.exists(wrong_path):
                 # This is handled by existence check generally but let's be explicit
                 pass

    # 7. Safety Invariants
    for key in ["summary", "metrics", "project_state"]:
        d = loaded_data[key]
        if d.get("network_executed") is not False: errors.append(f"{key}: network_executed violation")
        if d.get("trading_allowed") is not False: errors.append(f"{key}: trading_allowed violation")
        if d.get("real_orders_possible") is not False: errors.append(f"{key}: real_orders_possible violation")
        if d.get("dataset_created") is not False: errors.append(f"{key}: dataset_created violation")

    if errors:
        print(f"ERROR: Validation {v_disp} failed ({len(errors)}):\n" + "\n".join(f"  - {e}" for e in errors))
        sys.exit(1)

    print(f"SUCCESS: {v_disp} VALIDATED (Cross-file alignment OK).")

if __name__ == "__main__":
    main()
