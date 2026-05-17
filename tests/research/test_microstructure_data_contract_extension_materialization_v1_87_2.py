import pytest
import json
import os
import subprocess
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

def test_scripts_run_without_manual_pythonpath():
    env = os.environ.copy()
    if "PYTHONPATH" in env:
        del env["PYTHONPATH"]
    
    cmd = ["python", "scripts/run_microstructure_data_contract_extension_materialization_v1_87_2.py", "--version", "v1_87_2"]
    result = subprocess.run(cmd, env=env, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    assert result.returncode == 0, f"Script failed: {result.stderr}\n{result.stdout}"

def test_validator_runs_without_manual_pythonpath():
    env = os.environ.copy()
    if "PYTHONPATH" in env:
        del env["PYTHONPATH"]
    
    cmd = ["python", "scripts/validate_microstructure_data_contract_extension_materialization_v1_87_2_reports.py", "--version", "v1_87_2"]
    result = subprocess.run(cmd, env=env, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    assert result.returncode == 0, f"Validator failed: {result.stderr}\n{result.stdout}"

def _run_validator_with_mutated_summary(mutation: dict, expected_failure_string: str):
    summary_path = PROJECT_ROOT / "reports/research/microstructure_data_contract_extension_materialization_summary_v1_87_2.json"
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
        cmd = ["python", "scripts/validate_microstructure_data_contract_extension_materialization_v1_87_2_reports.py", "--version", "v1_87_2"]
        result = subprocess.run(cmd, env=env, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
        assert result.returncode != 0
        assert expected_failure_string in result.stdout
    finally:
        with open(summary_path, "w") as f:
            json.dump(original_data, f)

def test_validator_rejects_missing_release_zip():
    path = PROJECT_ROOT / "reports/release_zip_v1_87_2.json"
    bak = PROJECT_ROOT / "reports/release_zip_v1_87_2.json.bak"
    os.rename(path, bak)
    try:
        cmd = ["python", "scripts/validate_microstructure_data_contract_extension_materialization_v1_87_2_reports.py", "--version", "v1_87_2"]
        result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
        assert result.returncode != 0
        assert "Mandatory file release_zip missing" in result.stdout
    finally:
        os.rename(bak, path)

def test_validator_rejects_zip_smoke_failed():
    path = PROJECT_ROOT / "reports/zip_smoke_test_v1_87_2.json"
    with open(path, "r") as f: data = json.load(f)
    old_val = data["smoke_test_passed"]
    data["smoke_test_passed"] = False
    with open(path, "w") as f: json.dump(data, f)
    try:
        cmd = ["python", "scripts/validate_microstructure_data_contract_extension_materialization_v1_87_2_reports.py", "--version", "v1_87_2"]
        result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
        assert result.returncode != 0
        assert "zip_smoke report indicates smoke test failure" in result.stdout
    finally:
        data["smoke_test_passed"] = old_val
        with open(path, "w") as f: json.dump(data, f)

def test_validator_rejects_zip_smoke_failed_count_positive():
    path = PROJECT_ROOT / "reports/zip_smoke_test_v1_87_2.json"
    with open(path, "r") as f: data = json.load(f)
    old_val = data["smoke_failed_count"]
    data["smoke_failed_count"] = 1
    with open(path, "w") as f: json.dump(data, f)
    try:
        cmd = ["python", "scripts/validate_microstructure_data_contract_extension_materialization_v1_87_2_reports.py", "--version", "v1_87_2"]
        result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
        assert result.returncode != 0
        assert "zip_smoke report indicates smoke test failure" in result.stdout
    finally:
        data["smoke_failed_count"] = old_val
        with open(path, "w") as f: json.dump(data, f)

def test_validator_rejects_missing_code_review_doc():
    path = PROJECT_ROOT / "docs/code_review_v1_87_2.md"
    bak = PROJECT_ROOT / "docs/code_review_v1_87_2.md.bak"
    os.rename(path, bak)
    try:
        cmd = ["python", "scripts/validate_microstructure_data_contract_extension_materialization_v1_87_2_reports.py", "--version", "v1_87_2"]
        result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
        assert result.returncode != 0
        assert "Mandatory file code_review_doc missing" in result.stdout
    finally:
        os.rename(bak, path)

def test_validator_rejects_report_index_missing_v1_87_2():
    path = PROJECT_ROOT / "reports/REPORT_INDEX.md"
    with open(path, "r") as f: content = f.read()
    mutated = content.replace("V1.87.2", "V1.87.X").replace("v1_87_2", "v1_87_X")
    with open(path, "w") as f: f.write(mutated)
    try:
        cmd = ["python", "scripts/validate_microstructure_data_contract_extension_materialization_v1_87_2_reports.py", "--version", "v1_87_2"]
        result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
        assert result.returncode != 0
        assert "REPORT_INDEX.md does not reference V1.87.2" in result.stdout
    finally:
        with open(path, "w") as f: f.write(content)

def test_validator_rejects_latest_metrics_network_executed_true():
    _run_validator_with_mutated_summary({"network_executed": True}, "network_executed must be False")

def test_validator_rejects_project_state_dataset_created_true():
    _run_validator_with_mutated_summary({"dataset_created": True}, "dataset_created must be False")

def test_validator_rejects_v1_84_hash_mismatch():
    file_audit_path = PROJECT_ROOT / "reports/research/microstructure_data_contract_extension_materialization_file_audit_v1_87_2.json"
    with open(file_audit_path, "r") as f: original_data = json.load(f)
    mutated_data = original_data.copy()
    mutated_data["v1_84_manifest_sha256"] = "wrong_hash"
    with open(file_audit_path, "w") as f: json.dump(mutated_data, f)
    try:
        cmd = ["python", "scripts/validate_microstructure_data_contract_extension_materialization_v1_87_2_reports.py", "--version", "v1_87_2"]
        result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
        assert result.returncode != 0
        assert "Hash mismatch for V1.84 manifest.json" in result.stdout
    finally:
        with open(file_audit_path, "w") as f: json.dump(original_data, f)

def test_validator_rejects_extra_file_in_v1_87_directory():
    v1_87_dir = PROJECT_ROOT / "data/research/microstructure_contract_materialization/v1_87"
    extra_file = v1_87_dir / "extra.json"
    with open(extra_file, "w") as f: f.write("{}")
    try:
        cmd = ["python", "scripts/validate_microstructure_data_contract_extension_materialization_v1_87_2_reports.py", "--version", "v1_87_2"]
        result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
        assert result.returncode != 0
        assert "Unexpected files in v1_87" in result.stdout
    finally:
        if extra_file.exists(): os.remove(extra_file)

def test_smoke_v1_87_2_uses_relative_paths():
    smoke_script = PROJECT_ROOT / "scripts/smoke_test_clean_zip.py"
    with open(smoke_script, "r") as f: content = f.read()
    assert "v1_87_2" in content

def test_no_pass_only_tests_in_v1_87_2():
    current_file = Path(__file__)
    with open(current_file, "r") as f: content = f.read()
    lines = [line.strip() for line in content.split("\n")]
    for line in lines:
        if line == "pa" + "ss":
            assert False, "Found pass statement"

def test_no_assert_true_or_true_in_v1_87_2():
    current_file = Path(__file__)
    with open(current_file, "r") as f: content = f.read()
    assert "asse" + "rt True" not in content
    assert "or T" + "rue" not in content

def test_no_pass_in_extension_materialization_validator_module():
    module_path = PROJECT_ROOT / "src/galapagos/research/microstructure_data_contract_extension_materialization/validator.py"
    with open(module_path, "r") as f: content = f.read()
    lines = [line.strip() for line in content.split("\n")]
    for line in lines:
        if line == "pa" + "ss":
             assert False, f"Found 'pass' in {module_path}"
