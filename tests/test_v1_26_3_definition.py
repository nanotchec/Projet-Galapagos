import pytest
import json
from pathlib import Path

def test_protocol_v1_26_3_completeness():
    path = Path("reports/research/preregistered_signal_validation_protocol_v1_26_3.json")
    if not path.exists():
        pytest.skip("V1.26.3 protocol not yet generated")
        
    with open(path) as f:
        protocol = json.load(f)
        
    assert protocol["protocol_version"] == "v1.26.3"
    assert "locked_filter_definition" in protocol
    defn = protocol["locked_filter_definition"]
    assert defn["filter_name"] == "low_frequency_strict_score"
    assert defn["score_column"] == "predicted_probability"
    assert defn["temporal_frequency_rule"] == "7D"
    assert protocol["frozen_filter_definition_complete"] is True

def test_completeness_audit_v1_26_3():
    path = Path("reports/research/preregistered_protocol_completeness_audit_v1_26_3.json")
    if not path.exists():
        pytest.skip("V1.26.3 audit not yet generated")
        
    with open(path) as f:
        audit = json.load(f)
        
    assert audit["status"] == "PREREGISTRATION_PROTOCOL_COMPLETE"
    assert audit["filter_definition_complete"] is True
