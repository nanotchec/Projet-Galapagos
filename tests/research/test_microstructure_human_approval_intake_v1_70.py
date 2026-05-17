import pytest
import subprocess
import sys
import json
import shutil
from pathlib import Path

@pytest.fixture
def mock_env(tmp_path):
    root = tmp_path
    (root / "reports/research").mkdir(parents=True)
    (root / "reports/current").mkdir(parents=True)
    (root / "docs").mkdir(parents=True)
    (root / "scripts").mkdir(parents=True)
    
    # Mock V1.70.1 summary
    v1_70_1_summary = {
        "version": "V1.70.1",
        "path_portability_hardened": True,
        "machine_specific_paths_scan_passed": True,
        "machine_specific_paths_found": []
    }
    with open(root / "reports/research/microstructure_human_approval_summary_v1_70_1.json", "w") as f:
        json.dump(v1_70_1_summary, f)
        
    # Copy scripts to mock env
    shutil.copy("scripts/run_microstructure_human_approval_intake.py", root / "scripts/")
    shutil.copy("scripts/validate_microstructure_human_approval_intake_reports.py", root / "scripts/")
    shutil.copy("scripts/_bootstrap.py", root / "scripts/")
    
    # Symlink src to mock env
    real_root = Path(__file__).parent.parent.parent.resolve()
    (root / "src").symlink_to(real_root / "src")
    
    return root

def run_script(root, phrase_input):
    cmd = [
        sys.executable,
        "scripts/run_microstructure_human_approval_intake.py",
        "--pending-summary", "reports/research/microstructure_human_approval_summary_v1_70_1.json",
        "--pending-consistency", "dummy",
        "--path-portability-audit", "reports/research/microstructure_human_approval_summary_v1_70_1.json",
        "--previous-recommendation", "dummy",
        "--release-report", "dummy",
        "--audit-report", "dummy",
        "--smoke-report", "dummy",
        "--approval-phrase-input", phrase_input,
        "--version", "v1.70.2"
    ]
    return subprocess.run(cmd, cwd=root, capture_output=True, text=True, env={"PYTHONPATH": f"{root}:{root}/src"})

def test_empty_phrase(mock_env):
    res = run_script(mock_env, "")
    assert res.returncode == 0
    with open(mock_env / "reports/research/microstructure_human_approval_summary_v1_70_2.json") as f:
        summary = json.load(f)
    assert summary["human_approval_granted"] is False
    assert summary["final_verdict"] == "MICROSTRUCTURE_HUMAN_APPROVAL_INTAKE_PENDING"

def test_incorrect_phrase(mock_env):
    res = run_script(mock_env, "I approve everything")
    assert res.returncode == 0
    with open(mock_env / "reports/research/microstructure_human_approval_summary_v1_70_2.json") as f:
        summary = json.load(f)
    assert summary["human_approval_granted"] is False
    assert summary["approval_phrase_validated"] is False

def test_exact_phrase(mock_env):
    phrase = "I explicitly approve a one-request tiny network preflight with no data directory writes and no trading."
    res = run_script(mock_env, phrase)
    assert res.returncode == 0
    with open(mock_env / "reports/research/microstructure_human_approval_summary_v1_70_2.json") as f:
        summary = json.load(f)
    assert summary["human_approval_granted"] is True
    assert summary["approval_phrase_validated"] is True
    assert summary["network_enabled"] is False # Safety: still false in V1.70
    assert summary["requests_executed_count"] == 0

def test_validator_rejects_unsafe(mock_env):
    # Generate valid reports first
    phrase = "I explicitly approve a one-request tiny network preflight with no data directory writes and no trading."
    run_script(mock_env, phrase)
    summary_p = mock_env / "reports/research/microstructure_human_approval_summary_v1_70_2.json"
    
    with open(summary_p) as f:
        data = json.load(f)
    
    # Force network_enabled = True to test validator
    data["network_enabled"] = True
    with open(summary_p, "w") as f:
        json.dump(data, f)
        
    cmd = [sys.executable, "scripts/validate_microstructure_human_approval_intake_reports.py", "--version", "v1.70.2"]
    res = subprocess.run(cmd, cwd=mock_env, capture_output=True, text=True)
    assert res.returncode != 0
    assert "ERROR: Safety check failed for network_enabled" in res.stdout
