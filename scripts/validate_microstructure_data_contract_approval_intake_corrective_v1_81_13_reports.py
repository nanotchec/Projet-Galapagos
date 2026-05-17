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
    parser.add_argument("--version", default="v1_81_13")
    args = parser.parse_args()
    
    v_disp = "V1.81.13"
    v_norm = "v1_81_13"
    
    reports_to_check = {
        "pytest_audit": PROJECT_ROOT / f"reports/research/microstructure_data_contract_approval_intake_corrective_pytest_audit_{v_norm}.json",
        "neg_cov": PROJECT_ROOT / f"reports/research/microstructure_data_contract_approval_intake_corrective_negative_coverage_{v_norm}.json",
        "summary": PROJECT_ROOT / f"reports/research/microstructure_data_contract_approval_intake_corrective_summary_{v_norm}.json",
        "current_state": PROJECT_ROOT / f"reports/research/microstructure_data_contract_approval_intake_corrective_current_state_alignment_{v_norm}.json",
        "consistency": PROJECT_ROOT / f"reports/research/microstructure_data_contract_approval_intake_corrective_consistency_check_{v_norm}.json",
        "metrics": PROJECT_ROOT / "reports/current/latest_metrics.json",
        "project_state": PROJECT_ROOT / "reports/PROJECT_STATE.json",
        "zip_audit": PROJECT_ROOT / f"reports/zip_audit_{v_norm}.json",
        "release_zip": PROJECT_ROOT / f"reports/release_zip_{v_norm}.json"
    }
    
    docs_to_check = {
        "code_review": PROJECT_ROOT / f"docs/code_review_{v_norm}.md",
        "report_index": PROJECT_ROOT / "reports/REPORT_INDEX.md"
    }
    
    errors = []
    
    # Check existence of JSON reports (MANDATORY in V1.81.13)
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

    # 2. Pytest Alignment & Integrity (NO HARDCODED 133)
    counts = {}
    for key in ["pytest_audit", "summary", "metrics", "project_state"]:
        c = loaded_data[key].get("pytest_test_count_observed")
        counts[key] = c
        if loaded_data[key].get("pytest_exit_code") != 0:
            errors.append(f"{key} reports pytest failure (exit code != 0)")
        if loaded_data[key].get("pytest_failed_count", 0) != 0:
            errors.append(f"{key} reports failed tests")
        if loaded_data[key].get("unmapped_tests") != []:
            errors.append(f"{key} contains unmapped tests")
            
    if len(set(counts.values())) > 1:
        errors.append(f"Pytest count divergence across files: {counts}")
    
    first_count = list(counts.values())[0]
    if first_count is None or first_count < 120:
         errors.append(f"Pytest count too low: {first_count} < 120 (expecting >= 120)")

    # 3. Smoke Test validation is performed by the smoke test itself using this validator.
    # We do not cross-check the smoke report here to avoid circular dependency during packaging.
    
    # 4. Audit Deep Validation (MANDATORY)
    audit = loaded_data["zip_audit"]
    if not audit.get("clean_zip_ready_for_external_review"):
        errors.append("zip_audit: clean_zip_ready_for_external_review != true")
    if audit.get("audit_zip_project_state_version") != v_disp:
        errors.append(f"zip_audit: audit_zip_project_state_version ({audit.get('audit_zip_project_state_version')}) != {v_disp}")
    if audit.get("audit_zip_version_parse_correct") is not True:
        errors.append("zip_audit: audit_zip_version_parse_correct != true")

    # 5. Placeholder Check (Only in values, not keys)
    def _has_placeholder(obj):
        if isinstance(obj, str):
            if "placeholder" in obj.lower(): return True
        elif isinstance(obj, list):
            return any(_has_placeholder(x) for x in obj)
        elif isinstance(obj, dict):
            return any(_has_placeholder(v) for v in obj.values())
        return False

    for key, path in reports_to_check.items():
        if _has_placeholder(loaded_data[key]):
            errors.append(f"Placeholder value found in report: {path.name}")
        
        # Check in corresponding MD if exists
        md_path = path.with_suffix(".md")
        if md_path.exists():
            content = md_path.read_text()
            # On cherche "placeholder" mais on ignore la ligne de la clé "no_placeholder_reports" si elle est affichée
            # En fait, on va juste chercher les phrases spécifiques interdites
            if "alignment placeholder" in content.lower() or "check placeholder" in content.lower():
                errors.append(f"Forbidden placeholder phrase found in doc: {md_path.name}")

    # 6. Report Index Check
    index_content = docs_to_check["report_index"].read_text()
    if v_disp not in index_content:
        errors.append(f"REPORT_INDEX.md does not reference {v_disp}")

    # 7. Script Structure Check (No duplicate main)
    scripts_to_check = [
        PROJECT_ROOT / f"scripts/run_microstructure_data_contract_approval_intake_corrective_{v_norm}.py",
        PROJECT_ROOT / f"scripts/validate_microstructure_data_contract_approval_intake_corrective_{v_norm}.py"
    ]
    for s_path in scripts_to_check:
        if s_path.exists():
            s_content = s_path.read_text()
            if s_content.count('if __name__ == "__main__":') > 1:
                errors.append(f"Duplicate main block in script: {s_path.name}")

    # 8. Safety Invariants (Propagated everywhere)
    for key in ["summary", "metrics", "project_state"]:
        d = loaded_data[key]
        if d.get("network_executed") is not False: errors.append(f"{key}: network_executed violation")
        if d.get("trading_allowed") is not False: errors.append(f"{key}: trading_allowed violation")
        if d.get("real_orders_possible") is not False: errors.append(f"{key}: real_orders_possible violation")
        if d.get("dataset_created") is not False: errors.append(f"{key}: dataset_created violation")
        if d.get("v1_82_execution_attempted") is not False: errors.append(f"{key}: v1_82_execution_attempted violation")
        if d.get("no_stub_reports") is not True: errors.append(f"{key}: no_stub_reports != true")

    if errors:
        print(f"ERROR: Validation {v_disp} failed ({len(errors)}):\n" + "\n".join(f"  - {e}" for e in errors))
        sys.exit(1)

    print(f"SUCCESS: {v_disp} VALIDATED (Cross-file alignment OK).")

if __name__ == "__main__":
    main()
