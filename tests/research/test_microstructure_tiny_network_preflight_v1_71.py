import json
import pytest
import subprocess
import sys
import shutil
from pathlib import Path

@pytest.fixture
def mock_env(tmp_path):
    root = tmp_path / "projet-galapagos"
    root.mkdir()
    (root / "reports/research").mkdir(parents=True)
    (root / "reports/current").mkdir(parents=True)
    (root / "docs").mkdir(parents=True)
    (root / "scripts").mkdir(parents=True)
    
    # Mock V1.70.2 summary
    v1_70_2_summary = {
        "version": "V1.70.2",
        "human_approval_granted": True,
        "approval_phrase_validated": True,
        "v1_71_network_preflight_authorized": True,
        "max_request_count": 1,
        "no_data_directory_writes": True,
        "no_real_trading": True
    }
    with open(root / "reports/research/microstructure_human_approval_summary_v1_70_2.json", "w") as f:
        json.dump(v1_70_2_summary, f)
        
    # Copy scripts to mock env
    shutil.copy("scripts/run_microstructure_tiny_network_preflight.py", root / "scripts/")
    shutil.copy("scripts/validate_microstructure_tiny_network_preflight_reports.py", root / "scripts/")
    
    # Create _bootstrap.py
    with open(root / "scripts/_bootstrap.py", "w") as f:
        f.write("def bootstrap_src_path(): pass\n")
        
    return root

def run_script(root, version="v1.71"):
    cmd = [
        sys.executable,
        "scripts/run_microstructure_tiny_network_preflight.py",
        "--human-approval-summary", "reports/research/microstructure_human_approval_summary_v1_70_2.json",
        "--human-approval-consistency", "dummy",
        "--v1-71-execution-plan", "dummy",
        "--v1-70-2-recommendation", "dummy",
        "--release-report", "dummy",
        "--audit-report", "dummy",
        "--smoke-report", "dummy",
        "--version", version
    ]
    # We might want to mock requests here, but for simple structural tests we just run it.
    # Note: If no internet, TinyNetworkClient should fail safely.
    return subprocess.run(cmd, cwd=root, capture_output=True, text=True, env={"PYTHONPATH": f"{root}:{Path.cwd()}/src"})

def test_structural_generation(mock_env):
    res = run_script(mock_env)
    # Even if network fails, script should return 0 (safe failure)
    assert res.returncode == 0
    v_norm = "v1_71"
    summary_p = mock_env / f"reports/research/microstructure_tiny_network_summary_{v_norm}.json"
    assert summary_p.exists()
    
    with open(summary_p) as f:
        summary = json.load(f)
    assert summary["version"] == "V1.71"
    assert summary["max_request_count"] == 1

def test_validator_detects_excessive_requests(mock_env):
    run_script(mock_env)
    v_norm = "v1_71"
    summary_p = mock_env / f"reports/research/microstructure_tiny_network_summary_{v_norm}.json"
    
    with open(summary_p) as f:
        data = json.load(f)
    
    # Force failure
    data["requests_executed_count"] = 5
    with open(summary_p, "w") as f:
        json.dump(data, f)
        
    cmd = [sys.executable, "scripts/validate_microstructure_tiny_network_preflight_reports.py", "--version", "v1.71"]
    res = subprocess.run(cmd, cwd=mock_env, capture_output=True, text=True)
    assert res.returncode != 0
    assert "ERROR: Too many requests executed" in res.stdout

def test_validator_rejects_data_writes(mock_env):
    run_script(mock_env)
    v_norm = "v1_71"
    summary_p = mock_env / f"reports/research/microstructure_tiny_network_summary_{v_norm}.json"
    
    with open(summary_p) as f:
        data = json.load(f)
    
    data["no_data_directory_writes"] = False
    with open(summary_p, "w") as f:
        json.dump(data, f)
        
    cmd = [sys.executable, "scripts/validate_microstructure_tiny_network_preflight_reports.py", "--version", "v1.71"]
    res = subprocess.run(cmd, cwd=mock_env, capture_output=True, text=True)
    assert res.returncode != 0
    assert "ERROR: no_data_directory_writes must be True" in res.stdout

def test_validator_rejects_large_preview(mock_env):
    run_script(mock_env)
    v_norm = "v1_71"
    summary_p = mock_env / f"reports/research/microstructure_tiny_network_summary_{v_norm}.json"
    
    with open(summary_p) as f:
        data = json.load(f)
    
    data["records_preview_count"] = 100
    with open(summary_p, "w") as f:
        json.dump(data, f)
        
    cmd = [sys.executable, "scripts/validate_microstructure_tiny_network_preflight_reports.py", "--version", "v1.71"]
    res = subprocess.run(cmd, cwd=mock_env, capture_output=True, text=True)
    assert res.returncode != 0
    assert "ERROR: Too many records in preview" in res.stdout
