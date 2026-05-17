import pytest
from galapagos.research.microstructure_bounded_reporting_fix.reporting_audit import ReportingAudit

def test_reporting_audit_incomplete():
    audit = ReportingAudit()
    v1_77_summary = {
        "successful_response_count": 10,
        "response_status_codes": [None]
    }
    v1_77_client = {} # Missing codes here too
    res = audit.perform_audit(v1_77_summary, v1_77_client)
    assert res["previous_status_reporting_incomplete"] is True
    assert res["response_status_reporting_fixed"] is False
    assert res["response_status_codes_available"] is False
    assert res["response_status_codes_all_present"] is False
    assert res["response_status_codes"] == []

def test_reporting_audit_fixed():
    audit = ReportingAudit()
    v1_77_summary = {
        "successful_response_count": 2,
        "response_status_codes": [None]
    }
    v1_77_client = {
        "response_status_codes": [200, 200]
    }
    res = audit.perform_audit(v1_77_summary, v1_77_client)
    assert res["previous_status_reporting_incomplete"] is True
    assert res["response_status_reporting_fixed"] is True
    assert res["response_status_codes_available"] is True
    assert res["response_status_codes"] == [200, 200]

def test_reporting_audit_already_ok():
    audit = ReportingAudit()
    v1_77_summary = {
        "successful_response_count": 2,
        "response_status_codes": [200, 200]
    }
    v1_77_client = {
        "response_status_codes": [200, 200]
    }
    res = audit.perform_audit(v1_77_summary, v1_77_client)
    assert res["previous_status_reporting_incomplete"] is False
    assert res["response_status_reporting_fixed"] is False
    assert res["response_status_codes_available"] is True
    assert res["response_status_codes"] == [200, 200]
