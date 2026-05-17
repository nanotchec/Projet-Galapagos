import pytest
from galapagos.research.microstructure_bounded_mini_collection_approval.approval_phrase_validator import ApprovalPhraseValidator
from galapagos.research.microstructure_bounded_mini_collection_approval.safety_verdict_engine import SafetyVerdictEngine

def test_phrase_validator_empty():
    validator = ApprovalPhraseValidator()
    res = validator.validate_phrase("")
    assert res["approval_phrase_validated"] is False
    assert res["human_approval_granted"] is False

def test_phrase_validator_incorrect():
    validator = ApprovalPhraseValidator()
    res = validator.validate_phrase("I approve.")
    assert res["approval_phrase_validated"] is False
    assert res["human_approval_granted"] is False

def test_phrase_validator_exact():
    validator = ApprovalPhraseValidator()
    exact = "I explicitly approve a bounded reports-only mini-collection with at most 10 public requests, no data directory writes, no dataset creation, and no trading."
    res = validator.validate_phrase(exact)
    assert res["approval_phrase_validated"] is True
    assert res["human_approval_granted"] is True

def test_safety_verdict_validated():
    engine = SafetyVerdictEngine()
    context = {"approval_phrase_validated": True}
    res = engine.compute_verdict(context)
    assert res["final_verdict"] == "MICROSTRUCTURE_BOUNDED_MINI_COLLECTION_APPROVAL_VALIDATED"
    assert res["v1_77_bounded_mini_collection_authorized"] is True

def test_safety_verdict_pending():
    engine = SafetyVerdictEngine()
    context = {"approval_phrase_validated": False}
    res = engine.compute_verdict(context)
    assert res["final_verdict"] == "MICROSTRUCTURE_BOUNDED_MINI_COLLECTION_APPROVAL_PENDING"
    assert res["v1_77_bounded_mini_collection_authorized"] is False
