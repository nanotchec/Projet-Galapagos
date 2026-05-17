import pytest
from galapagos.research.microstructure_two_request_preflight.two_request_guard import TwoRequestGuard
from galapagos.research.microstructure_two_request_preflight.input_guard import InputGuard

def test_two_request_guard_limit():
    guard = TwoRequestGuard(max_requests=2)
    assert guard.authorize_request() is True
    assert guard.authorize_request() is True
    assert guard.authorize_request() is False
    assert guard.counter == 2
    
    status = guard.get_status()
    assert status["two_request_limit_enforced"] is True
    assert status["requests_executed_count"] == 2
    assert status["limit_respected"] is True

def test_input_guard_v1_73_1_valid():
    guard = InputGuard()
    valid_summary = {
        "version": "V1.73.1",
        "approval_phrase_validated": True,
        "human_approval_granted": True,
        "v1_74_two_request_preflight_authorized": True,
        "max_request_count": 2,
        "v1_74_no_data_directory_writes": True,
        "v1_74_no_trading": True
    }
    res = guard.validate_v1_73_1_state(valid_summary)
    assert res["input_guard_passed"] is True

def test_input_guard_v1_73_1_invalid_version():
    guard = InputGuard()
    invalid_summary = {
        "version": "V1.73", # Wrong version
        "approval_phrase_validated": True,
        "human_approval_granted": True,
        "v1_74_two_request_preflight_authorized": True,
        "max_request_count": 2,
        "v1_74_no_data_directory_writes": True,
        "v1_74_no_trading": True
    }
    res = guard.validate_v1_73_1_state(invalid_summary)
    assert res["input_guard_passed"] is False

def test_input_guard_v1_73_1_no_approval():
    guard = InputGuard()
    invalid_summary = {
        "version": "V1.73.1",
        "approval_phrase_validated": False,
        "human_approval_granted": False,
        "v1_74_two_request_preflight_authorized": False,
        "max_request_count": 2,
        "v1_74_no_data_directory_writes": True,
        "v1_74_no_trading": True
    }
    res = guard.validate_v1_73_1_state(invalid_summary)
    assert res["input_guard_passed"] is False
