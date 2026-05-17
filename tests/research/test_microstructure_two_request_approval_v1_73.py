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
    
    # Mock V1.72 summary
    v1_72_summary = {
        "version": "V1.72",
        "one_request_preflight_review_passed": True,
        "collection_expansion_approved": False,
        "future_expansion_requires_new_human_approval": True,
        "max_future_request_count_without_new_approval": 0
    }
    with open(root / "reports/research/microstructure_one_request_review_summary_v1_72.json", "w") as f:
        json.dump(v1_72_summary, f)
        
    # Mock V1.72 gate
    v1_72_gate = {
        "expansion_readiness_gate_created": True,
        "gate_status": "LOCKED_PENDING_NEW_HUMAN_APPROVAL"
    }
    with open(root / "reports/research/microstructure_expansion_readiness_gate_v1_72.json", "w") as f:
        json.dump(v1_72_gate, f)
        
    # Copy scripts to mock env
    shutil.copy("scripts/run_microstructure_two_request_approval.py", root / "scripts/")
    shutil.copy("scripts/validate_microstructure_two_request_approval_reports.py", root / "scripts/")
    
    # Create _bootstrap.py
    with open(root / "scripts/_bootstrap.py", "w") as f:
        f.write("def bootstrap_src_path(): pass\n")
        
    return root

def run_script(root, phrase="", version="v1.73"):
    cmd = [
        sys.executable,
        "scripts/run_microstructure_two_request_approval.py",
        "--one-request-review-summary", "reports/research/microstructure_one_request_review_summary_v1_72.json",
        "--one-request-review-consistency", "dummy",
        "--expansion-readiness-gate", "reports/research/microstructure_expansion_readiness_gate_v1_72.json",
        "--v1-72-recommendation", "dummy",
        "--release-report", "dummy",
        "--audit-report", "dummy",
        "--smoke-report", "dummy",
        "--approval-phrase-input", phrase,
        "--version", version
    ]
    return subprocess.run(cmd, cwd=root, capture_output=True, text=True, env={"PYTHONPATH": f"{root}:{Path.cwd()}/src"})

def test_empty_phrase_approval_false(mock_env):
    res = run_script(mock_env, phrase="")
    assert res.returncode == 0
    summary_p = mock_env / "reports/research/microstructure_two_request_approval_summary_v1_73.json"
    with open(summary_p) as f:
        summary = json.load(f)
    assert summary["human_approval_granted"] is False
    assert summary["v1_74_two_request_preflight_authorized"] is False

def test_incorrect_phrase_approval_false(mock_env):
    res = run_script(mock_env, phrase="I approve")
    assert res.returncode == 0
    summary_p = mock_env / "reports/research/microstructure_two_request_approval_summary_v1_73.json"
    with open(summary_p) as f:
        summary = json.load(f)
    assert summary["human_approval_granted"] is False

def test_exact_phrase_approval_true(mock_env):
    phrase = "I explicitly approve a two-request tiny network preflight with reports-only output, no data directory writes, and no trading."
    res = run_script(mock_env, phrase=phrase)
    assert res.returncode == 0
    summary_p = mock_env / "reports/research/microstructure_two_request_approval_summary_v1_73.json"
    with open(summary_p) as f:
        summary = json.load(f)
    assert summary["human_approval_granted"] is True
    assert summary["v1_74_two_request_preflight_authorized"] is True
    assert summary["network_enabled"] is False

def test_validator_rejects_network_enabled(mock_env):
    run_script(mock_env)
    summary_p = mock_env / "reports/research/microstructure_two_request_approval_summary_v1_73.json"
    with open(summary_p) as f:
        data = json.load(f)
    data["network_enabled"] = True
    with open(summary_p, "w") as f:
        json.dump(data, f)
    cmd = [sys.executable, "scripts/validate_microstructure_two_request_approval_reports.py", "--version", "v1.73"]
    res = subprocess.run(cmd, cwd=mock_env, capture_output=True, text=True)
    assert res.returncode != 0
    assert "ERROR: network_enabled must be False" in res.stdout

def test_validator_rejects_requests_executed(mock_env):
    run_script(mock_env)
    summary_p = mock_env / "reports/research/microstructure_two_request_approval_summary_v1_73.json"
    with open(summary_p) as f:
        data = json.load(f)
    data["requests_executed_count"] = 1
    with open(summary_p, "w") as f:
        json.dump(data, f)
    cmd = [sys.executable, "scripts/validate_microstructure_two_request_approval_reports.py", "--version", "v1.73"]
    res = subprocess.run(cmd, cwd=mock_env, capture_output=True, text=True)
    assert res.returncode != 0
    assert "ERROR: requests_executed_count must be 0" in res.stdout
