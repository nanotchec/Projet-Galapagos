import pytest
from galapagos.research.microstructure_data_contract_readiness.http_review import HTTPReview
from galapagos.research.microstructure_data_contract_readiness.no_write_guard import NoWriteGuard

def test_http_review_passed():
    reviewer = HTTPReview()
    summary = {
        "successful_response_count": 10,
        "response_status_codes": [200] * 10,
        "response_status_codes_none_present": False,
        "response_status_codes_all_present": True,
        "response_status_codes_all_success": True
    }
    res = reviewer.review_v1_79(summary, {})
    assert res["v1_79_http_review_passed"] is True

def test_http_review_failed_none():
    reviewer = HTTPReview()
    summary = {
        "successful_response_count": 10,
        "response_status_codes": [200] * 9 + [None],
        "response_status_codes_none_present": True,
        "response_status_codes_all_present": False,
        "response_status_codes_all_success": False
    }
    res = reviewer.review_v1_79(summary, {})
    assert res["v1_79_http_review_passed"] is False

def test_http_review_failed_count():
    reviewer = HTTPReview()
    summary = {
        "successful_response_count": 9,
        "response_status_codes": [200] * 9,
        "response_status_codes_none_present": False,
        "response_status_codes_all_present": True,
        "response_status_codes_all_success": True
    }
    res = reviewer.review_v1_79(summary, {})
    assert res["v1_79_http_review_passed"] is False

def test_no_write_guard_passed():
    guard = NoWriteGuard()
    v1_79_write = {"new_data_files_created": False}
    v1_79_summary = {"dataset_created": False, "no_data_directory_writes": True}
    res = guard.check_v1_79_v1_80(v1_79_write, v1_79_summary)
    assert res["no_write_guard_passed"] is True

def test_no_write_guard_failed():
    guard = NoWriteGuard()
    v1_79_write = {"new_data_files_created": True}
    v1_79_summary = {"dataset_created": False, "no_data_directory_writes": False}
    res = guard.check_v1_79_v1_80(v1_79_write, v1_79_summary)
    assert res["no_write_guard_passed"] is False
