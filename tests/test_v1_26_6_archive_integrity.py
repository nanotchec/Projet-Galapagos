import pytest
import json
from pathlib import Path

def test_archive_integrity_audit_status():
    path = Path("reports/research/preregistration_archive_integrity_v1_26_6.json")
    if not path.exists():
        pytest.skip("V1.26.6 archive audit not yet generated")
        
    with open(path) as f:
        report = json.load(f)
        
    assert report["archive_integrity_status"] == "PREREGISTRATION_ARCHIVE_HAS_SUPERSEDED_INCONSISTENCIES"
    assert report["reference_protocol"] == "v1.26.6"
    assert report["historical_protocols_superseded"] is True

def test_protocol_v1_26_6_reference():
    path = Path("reports/research/preregistered_signal_validation_protocol_v1_26_6.json")
    if not path.exists():
        pytest.skip("V1.26.6 protocol not yet generated")
        
    with open(path) as f:
        protocol = json.load(f)
        
    assert protocol["reference_protocol"] is True
    assert "v1.26.2" in protocol["supersedes"]
    assert "v1.26.3" in protocol["supersedes"]

def test_recommendation_v1_26_6_use_only():
    path = Path("reports/research/v1_26_6_recommendation.json")
    if not path.exists():
        pytest.skip("V1.26.6 recommendation not yet generated")
        
    with open(path) as f:
        reco = json.load(f)
        
    assert reco["reference_protocol"] == "v1.26.6"
    assert "v1.26.2" in reco["do_not_use_protocols_for_forward_validation"]
