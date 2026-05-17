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
    
    # Mock V1.71 summary
    v1_71_summary = {
        "version": "V1.71",
        "final_verdict": "MICROSTRUCTURE_ONE_REQUEST_TINY_NETWORK_PREFLIGHT_PASSED",
        "external_api_called": True,
        "tiny_network_collection_executed": True,
        "request_limit_enforced": True,
        "requests_executed_count": 1,
        "max_request_count": 1,
        "request_retry_count": 0,
        "pagination_used": False,
        "endpoint_allowed": True,
        "endpoint_authentication_required": False,
        "secrets_used": False,
        "authenticated_request_allowed": False,
        "records_preview_count": 10,
        "records_preview_count_lte_10": True,
        "reports_only_output": True,
        "no_data_directory_writes": True,
        "dataset_created": False,
        "parquet_created": False,
        "csv_created": False,
        "sqlite_created": False,
        "jsonl_created": False,
        "db_created": False,
        "strategy_link_allowed": False,
        "no_strategy_validated": True,
        "trading_allowed": False,
        "no_real_trading": True,
        "real_orders_possible": False,
        "response_status_code": 200,
        "response_size_bytes": 1724
    }
    with open(root / "reports/research/microstructure_tiny_network_summary_v1_71.json", "w") as f:
        json.dump(v1_71_summary, f)
        
    # Copy scripts to mock env
    shutil.copy("scripts/run_microstructure_one_request_review.py", root / "scripts/")
    shutil.copy("scripts/validate_microstructure_one_request_review_reports.py", root / "scripts/")
    
    # Create _bootstrap.py
    with open(root / "scripts/_bootstrap.py", "w") as f:
        f.write("def bootstrap_src_path(): pass\n")
        
    return root

def run_script(root, version="v1.72"):
    cmd = [
        sys.executable,
        "scripts/run_microstructure_one_request_review.py",
        "--tiny-network-summary", "reports/research/microstructure_tiny_network_summary_v1_71.json",
        "--tiny-network-consistency", "dummy",
        "--tiny-network-client", "dummy",
        "--response-preview", "dummy",
        "--one-request-guard", "dummy",
        "--no-data-write-guard", "dummy",
        "--safety-audit", "dummy",
        "--v1-71-recommendation", "dummy",
        "--release-report", "dummy",
        "--audit-report", "dummy",
        "--smoke-report", "dummy",
        "--version", version
    ]
    return subprocess.run(cmd, cwd=root, capture_output=True, text=True, env={"PYTHONPATH": f"{root}:{Path.cwd()}/src"})

def test_review_generation(mock_env):
    res = run_script(mock_env)
    assert res.returncode == 0
    summary_p = mock_env / "reports/research/microstructure_one_request_review_summary_v1_72.json"
    assert summary_p.exists()
    
    with open(summary_p) as f:
        summary = json.load(f)
    assert summary["version"] == "V1.72"
    assert summary["one_request_preflight_review_passed"] is True
    assert summary["new_network_requests_executed_count"] == 0

def test_validator_rejects_new_requests(mock_env):
    run_script(mock_env)
    summary_p = mock_env / "reports/research/microstructure_one_request_review_summary_v1_72.json"
    
    with open(summary_p) as f:
        data = json.load(f)
    
    data["new_network_requests_executed_count"] = 1
    with open(summary_p, "w") as f:
        json.dump(data, f)
        
    cmd = [sys.executable, "scripts/validate_microstructure_one_request_review_reports.py", "--version", "v1.72"]
    res = subprocess.run(cmd, cwd=mock_env, capture_output=True, text=True)
    assert res.returncode != 0
    assert "ERROR: new_network_requests_executed_count must be 0" in res.stdout

def test_validator_rejects_expansion_approval(mock_env):
    run_script(mock_env)
    summary_p = mock_env / "reports/research/microstructure_one_request_review_summary_v1_72.json"
    
    with open(summary_p) as f:
        data = json.load(f)
    
    data["collection_expansion_approved"] = True
    with open(summary_p, "w") as f:
        json.dump(data, f)
        
    cmd = [sys.executable, "scripts/validate_microstructure_one_request_review_reports.py", "--version", "v1.72"]
    res = subprocess.run(cmd, cwd=mock_env, capture_output=True, text=True)
    assert res.returncode != 0
    assert "ERROR: collection_expansion_approved must be False" in res.stdout

def test_validator_rejects_excessive_previous_requests(mock_env):
    run_script(mock_env)
    summary_p = mock_env / "reports/research/microstructure_one_request_review_summary_v1_72.json"
    
    with open(summary_p) as f:
        data = json.load(f)
    
    data["previous_requests_executed_count"] = 5
    with open(summary_p, "w") as f:
        json.dump(data, f)
        
    cmd = [sys.executable, "scripts/validate_microstructure_one_request_review_reports.py", "--version", "v1.72"]
    res = subprocess.run(cmd, cwd=mock_env, capture_output=True, text=True)
    assert res.returncode != 0
    assert "ERROR: previous_requests_executed_count must be 1" in res.stdout
