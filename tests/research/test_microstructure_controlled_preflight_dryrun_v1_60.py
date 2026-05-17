import pytest
import json
from pathlib import Path
from galapagos.research.microstructure_controlled_preflight_dryrun.input_guard import validate_input
from galapagos.research.microstructure_controlled_preflight_dryrun.network_block_verifier import verify_network_block
from galapagos.research.microstructure_controlled_preflight_dryrun.write_block_verifier import verify_write_block

def test_input_guard_valid_baseline():
    baseline = {
        "version": "V1.59.1",
        "preflight_plan_ready": True,
        "network_enabled": False,
        "real_collection_approved": False
    }
    report = validate_input(baseline)
    assert report["status"] == "PASSED"

def test_input_guard_invalid_baseline():
    baseline = {
        "version": "V1.58.2",
        "preflight_plan_ready": True,
        "network_enabled": False,
        "real_collection_approved": False
    }
    report = validate_input(baseline)
    assert report["status"] == "FAILED"
    assert "Invalid baseline version" in report["issues"][0]

def test_network_block_verifier():
    report = verify_network_block()
    assert report["status"] == "PASSED"
    assert report["network_enabled"] is False
    assert report["requests_executed_count"] == 0

def test_write_block_verifier_no_issues():
    # Assumes no forbidden files exist in data/ during test
    report = verify_write_block()
    assert report["status"] == "PASSED"
