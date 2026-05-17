import pytest
from galapagos.research.microstructure_two_request_review.input_guard import InputGuard
from galapagos.research.microstructure_two_request_review.request_limit_review import RequestLimitReview

def test_input_guard_v1_74_valid():
    guard = InputGuard()
    valid_summary = {
        "version": "V1.74",
        "final_verdict": "MICROSTRUCTURE_TWO_REQUEST_TINY_NETWORK_PREFLIGHT_PASSED",
        "requests_executed_count": 2,
        "reports_only_output": True,
        "no_data_directory_writes": True
    }
    res = guard.validate_v1_74_state(valid_summary)
    assert res["input_guard_passed"] is True

def test_input_guard_v1_74_invalid_count():
    guard = InputGuard()
    invalid_summary = {
        "version": "V1.74",
        "final_verdict": "MICROSTRUCTURE_TWO_REQUEST_TINY_NETWORK_PREFLIGHT_PASSED",
        "requests_executed_count": 3, # Exceeds limit
        "reports_only_output": True,
        "no_data_directory_writes": True
    }
    res = guard.validate_v1_74_state(invalid_summary)
    assert res["input_guard_passed"] is False

def test_request_limit_review_pass():
    engine = RequestLimitReview()
    summary = {"requests_executed_count": 2, "max_request_count": 2}
    res = engine.review_limit(summary)
    assert res["request_limit_review_passed"] is True

def test_request_limit_review_fail():
    engine = RequestLimitReview()
    summary = {"requests_executed_count": 3, "max_request_count": 2}
    res = engine.review_limit(summary)
    assert res["request_limit_review_passed"] is False
