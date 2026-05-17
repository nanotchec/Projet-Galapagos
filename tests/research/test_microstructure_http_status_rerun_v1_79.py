import pytest
from galapagos.research.microstructure_http_status_rerun.bounded_request_guard import BoundedRequestGuard
from galapagos.research.microstructure_http_status_rerun.rerun_verdict_engine import RerunVerdictEngine

def test_bounded_request_guard():
    guard = BoundedRequestGuard(max_requests=2)
    assert guard.can_request() is True
    guard.increment()
    assert guard.can_request() is True
    guard.increment()
    assert guard.can_request() is False

def test_rerun_verdict_engine_passed():
    engine = RerunVerdictEngine()
    audit_res = {"safety_audit_passed": True}
    net_summary = {"successful_requests": 1, "total_requests": 1}
    resp_summary = {
        "response_status_codes_all_present": True,
        "response_status_codes_all_success": True
    }
    res = engine.compute_verdict(audit_res, net_summary, resp_summary)
    assert res["final_verdict"] == "MICROSTRUCTURE_BOUNDED_HTTP_STATUS_RERUN_PASSED"

def test_rerun_verdict_engine_incomplete():
    engine = RerunVerdictEngine()
    audit_res = {"safety_audit_passed": True}
    net_summary = {"successful_requests": 1, "total_requests": 1}
    resp_summary = {
        "response_status_codes_all_present": False,
        "response_status_codes_all_success": True
    }
    res = engine.compute_verdict(audit_res, net_summary, resp_summary)
    assert res["final_verdict"] == "MICROSTRUCTURE_BOUNDED_HTTP_STATUS_RERUN_REPORTING_INCOMPLETE"

def test_rerun_verdict_engine_failed_safely():
    engine = RerunVerdictEngine()
    audit_res = {"safety_audit_passed": True}
    net_summary = {"successful_requests": 0, "total_requests": 1}
    resp_summary = {
        "response_status_codes_all_present": True,
        "response_status_codes_all_success": False
    }
    res = engine.compute_verdict(audit_res, net_summary, resp_summary)
    assert res["final_verdict"] == "MICROSTRUCTURE_BOUNDED_HTTP_STATUS_RERUN_ATTEMPT_FAILED_SAFELY"

def test_rerun_verdict_engine_safety_fail():
    engine = RerunVerdictEngine()
    audit_res = {"safety_audit_passed": False}
    net_summary = {"successful_requests": 1, "total_requests": 1}
    resp_summary = {
        "response_status_codes_all_present": True,
        "response_status_codes_all_success": True
    }
    res = engine.compute_verdict(audit_res, net_summary, resp_summary)
    assert res["final_verdict"] == "MICROSTRUCTURE_BOUNDED_HTTP_STATUS_RERUN_FAILED_SAFETY_AUDIT"
