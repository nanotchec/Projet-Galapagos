import pytest
from pathlib import Path
from galapagos.research.microstructure_preflight_fixture_execution.input_guard import InputGuard
from galapagos.research.microstructure_preflight_fixture_execution.preflight_fixture_executor import PreflightFixtureExecutor
from galapagos.research.microstructure_preflight_fixture_execution.runtime_audits import NetworkGateRuntimeAudit, WriteGateRuntimeAudit

def test_input_guard_pass():
    summary = {
        "version": "V1.65",
        "preflight_skeleton_created": True,
        "next_allowed_phase": "network_disabled_preflight_skeleton_fixture_execution",
        "network_enabled": False,
        "real_collection_approved": False,
        "requests_executed_count": 0
    }
    ig = InputGuard()
    assert ig.validate(summary) is True

def test_input_guard_fail_version():
    summary = {
        "version": "V1.64.2",
        "preflight_skeleton_created": True,
        "next_allowed_phase": "network_disabled_preflight_skeleton_fixture_execution",
        "network_enabled": False,
        "real_collection_approved": False,
        "requests_executed_count": 0
    }
    ig = InputGuard()
    assert ig.validate(summary) is False

def test_executor_simulation():
    executor = PreflightFixtureExecutor()
    fixtures = [{"data": [1, 2, 3]}, {"data": [4, 5]}]
    res = executor.execute(fixtures)
    assert res["preflight_skeleton_fixture_execution"] is True
    assert res["fixture_requests_loaded_count"] == 2
    assert res["fixture_records_processed_count"] == 5
    assert res["requests_executed_count"] == 0

def test_network_gate_runtime_audit():
    audit = NetworkGateRuntimeAudit()
    res = audit.audit()
    assert res["network_gate_runtime_checked"] is True
    assert res["requests_executed_count"] == 0

def test_write_gate_runtime_audit():
    audit = WriteGateRuntimeAudit()
    res = audit.audit()
    assert res["write_gate_runtime_checked"] is True
    assert res["no_data_directory_writes"] is True
