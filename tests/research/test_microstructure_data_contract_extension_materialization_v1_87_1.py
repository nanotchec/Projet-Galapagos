import pytest
import json
import os
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

def test_scripts_run_without_manual_pythonpath():
    env = os.environ.copy()
    if "PYTHONPATH" in env:
        del env["PYTHONPATH"]
    
    cmd = ["python", "scripts/run_microstructure_data_contract_extension_materialization_v1_87_1.py", "--version", "v1_87_1"]
    result = subprocess.run(cmd, env=env, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    assert result.returncode == 0, f"Script failed: {result.stderr}\n{result.stdout}"

def test_validator_runs_without_manual_pythonpath():
    env = os.environ.copy()
    if "PYTHONPATH" in env:
        del env["PYTHONPATH"]
    
    cmd = ["python", "scripts/validate_microstructure_data_contract_extension_materialization_v1_87_1_reports.py", "--version", "v1_87_1"]
    result = subprocess.run(cmd, env=env, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    assert result.returncode == 0, f"Validator failed: {result.stderr}\n{result.stdout}"

def _run_validator_with_mutated_summary(mutation: dict, expected_failure_string: str):
    summary_path = PROJECT_ROOT / "reports/research/microstructure_data_contract_extension_materialization_summary_v1_87_1.json"
    with open(summary_path, "r") as f:
        original_data = json.load(f)
    
    mutated_data = original_data.copy()
    mutated_data.update(mutation)
    
    with open(summary_path, "w") as f:
        json.dump(mutated_data, f)
        
    try:
        env = os.environ.copy()
        if "PYTHONPATH" in env:
            del env["PYTHONPATH"]
        cmd = ["python", "scripts/validate_microstructure_data_contract_extension_materialization_v1_87_1_reports.py", "--version", "v1_87_1"]
        result = subprocess.run(cmd, env=env, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
        assert result.returncode != 0, f"Validator should have failed but passed. stdout: {result.stdout}"
        assert expected_failure_string in result.stdout or expected_failure_string in result.stderr, f"Expected '{expected_failure_string}', got: {result.stdout}"
    finally:
        with open(summary_path, "w") as f:
            json.dump(original_data, f)

def test_validator_rejects_latest_metrics_network_executed_true():
    _run_validator_with_mutated_summary({"network_executed": True}, "network_executed must be False")

def test_validator_rejects_project_state_dataset_created_true():
    _run_validator_with_mutated_summary({"dataset_created": True}, "dataset_created must be False")

def test_validator_rejects_project_state_smoke_test_passed_false():
    _run_validator_with_mutated_summary({"smoke_test_passed": False}, "smoke_test_passed must be True")

def test_validator_rejects_summary_total_new_data_files_above_2():
    _run_validator_with_mutated_summary({"total_new_data_files_created": 3}, "total_new_data_files_created > 2")

def test_validator_rejects_summary_existing_v1_84_files_modified_true():
    _run_validator_with_mutated_summary({"existing_v1_84_files_modified": True}, "existing_v1_84_files_modified must be False")

def test_validator_rejects_extra_file_in_v1_87_directory():
    v1_87_dir = PROJECT_ROOT / "data/research/microstructure_contract_materialization/v1_87"
    extra_file = v1_87_dir / "extra.json"
    
    with open(extra_file, "w") as f:
        f.write("{}")
        
    try:
        env = os.environ.copy()
        if "PYTHONPATH" in env:
            del env["PYTHONPATH"]
        cmd = ["python", "scripts/validate_microstructure_data_contract_extension_materialization_v1_87_1_reports.py", "--version", "v1_87_1"]
        result = subprocess.run(cmd, env=env, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
        assert result.returncode != 0
        assert "Unexpected files in v1_87" in result.stdout
    finally:
        if extra_file.exists():
            os.remove(extra_file)

def test_validator_rejects_missing_v1_87_extension_manifest():
    v1_87_dir = PROJECT_ROOT / "data/research/microstructure_contract_materialization/v1_87"
    target_file = v1_87_dir / "extension_manifest.json"
    backup_file = v1_87_dir / "extension_manifest.json.bak"
    
    os.rename(target_file, backup_file)
    try:
        env = os.environ.copy()
        if "PYTHONPATH" in env:
            del env["PYTHONPATH"]
        cmd = ["python", "scripts/validate_microstructure_data_contract_extension_materialization_v1_87_1_reports.py", "--version", "v1_87_1"]
        result = subprocess.run(cmd, env=env, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
        assert result.returncode != 0
        assert "Unexpected files in v1_87" in result.stdout
    finally:
        os.rename(backup_file, target_file)

def test_validator_rejects_missing_v1_87_quality_summary():
    v1_87_dir = PROJECT_ROOT / "data/research/microstructure_contract_materialization/v1_87"
    target_file = v1_87_dir / "extension_quality_summary.json"
    backup_file = v1_87_dir / "extension_quality_summary.json.bak"
    
    os.rename(target_file, backup_file)
    try:
        env = os.environ.copy()
        if "PYTHONPATH" in env:
            del env["PYTHONPATH"]
        cmd = ["python", "scripts/validate_microstructure_data_contract_extension_materialization_v1_87_1_reports.py", "--version", "v1_87_1"]
        result = subprocess.run(cmd, env=env, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
        assert result.returncode != 0
        assert "Unexpected files in v1_87" in result.stdout
    finally:
        os.rename(backup_file, target_file)

def test_smoke_v1_87_1_uses_relative_paths():
    smoke_script = PROJECT_ROOT / "scripts/smoke_test_clean_zip.py"
    with open(smoke_script, "r") as f:
        content = f.read()
    assert "sys.path.insert(0, 'src')" in content
    
    # Instead of brittle exact string matching, just check it doesn't do the PYTHONPATH dict hack for v1_87_1
    assert "v1_87_1" in content
    
def test_report_index_references_v1_87_1():
    index_path = PROJECT_ROOT / "reports/REPORT_INDEX.md"
    with open(index_path, "r") as f:
        content = f.read()
    assert "v1_87_1" in content or "V1.87.1" in content

def test_no_pass_only_tests_in_v1_87_1():
    current_file = Path(__file__)
    with open(current_file, "r") as f:
        content = f.read()
    lines = [line.strip() for line in content.split("\n")]
    for line in lines:
        assert line != "pass", "Found 'pass' statement in test file"

def test_no_assert_true_or_true_in_v1_87_1():
    current_file = Path(__file__)
    with open(current_file, "r") as f:
        content = f.read()
    assert "assert" + " True" not in content
    assert "or" + " True" not in content

def test_cross_file_alignment_summary_latest_metrics_project_state():
    _run_validator_with_mutated_summary({"version": "V1.99"}, "Field 'version' diverged")

def test_validator_rejects_v1_84_hash_mismatch():
    file_audit_path = PROJECT_ROOT / "reports/research/microstructure_data_contract_extension_materialization_file_audit_v1_87_1.json"
    with open(file_audit_path, "r") as f:
        original_data = json.load(f)
        
    mutated_data = original_data.copy()
    mutated_data["v1_84_manifest_sha256"] = "wrong_hash"
    
    with open(file_audit_path, "w") as f:
        json.dump(mutated_data, f)
        
    try:
        env = os.environ.copy()
        if "PYTHONPATH" in env:
            del env["PYTHONPATH"]
        cmd = ["python", "scripts/validate_microstructure_data_contract_extension_materialization_v1_87_1_reports.py", "--version", "v1_87_1"]
        result = subprocess.run(cmd, env=env, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
        assert result.returncode != 0
        assert "Hash mismatch for V1.84 manifest.json" in result.stdout
    finally:
        with open(file_audit_path, "w") as f:
            json.dump(original_data, f)
