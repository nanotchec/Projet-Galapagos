import pytest
from galapagos.research.microstructure_http_status_rerun_approval.approval_phrase_validator import ApprovalPhraseValidator
from galapagos.research.microstructure_http_status_rerun_approval.http_status_capture_hardening import HTTPStatusCaptureHardening
from galapagos.research.microstructure_http_status_rerun_approval.validator_hardening import ValidatorHardening

def test_approval_phrase_validation():
    validator = ApprovalPhraseValidator()
    valid_phrase = "I explicitly approve a bounded reports-only HTTP-status rerun with at most 10 public requests, no data directory writes, no dataset creation, and no trading."
    
    res = validator.validate_phrase(valid_phrase)
    assert res["approval_phrase_validated"] is True
    assert res["human_approval_granted"] is True
    
    res = validator.validate_phrase("wrong phrase")
    assert res["approval_phrase_validated"] is False
    assert res["human_approval_granted"] is False

def test_status_capture_hardening():
    harder = HTTPStatusCaptureHardening()
    res = harder.get_hardening_status()
    assert res["http_status_capture_hardened"] is True
    assert "status_code" in res["status_capture_policy"]["fields"]
    assert "success_flag" in res["status_capture_policy"]["fields"]

def test_validator_hardening():
    harder = ValidatorHardening()
    res = harder.get_hardening_status()
    assert res["bounded_validator_hardened"] is True
    assert res["passed_verdict_requires_all_status_codes_present"] is True

def test_hardened_status_logic():
    # Simulation of the hardened logic that will be in V1.79 or updated validator
    def validate_response(resp):
        if resp.get("success_flag") is True:
            if not isinstance(resp.get("status_code"), int):
                return False
            if resp.get("status_code") is None:
                return False
            if not (200 <= resp.get("status_code") < 300):
                return False
        return True

    assert validate_response({"success_flag": True, "status_code": 200}) is True
    assert validate_response({"success_flag": True, "status_code": None}) is False
    assert validate_response({"success_flag": True, "status_code": "200"}) is False
    assert validate_response({"success_flag": True, "status_code": 404}) is False
