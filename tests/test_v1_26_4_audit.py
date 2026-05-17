import pytest
import json
from pathlib import Path
import re

def test_source_audit_regex():
    content = """
        _rule(
            "low_frequency_strict_score",
            "frequency",
            "Meilleur score par semaine.",
            highest_score_per_period("7D"),
            ("timestamp", "predicted_probability"),
        ),
    """
    rule_match = re.search(r'"low_frequency_strict_score".*?highest_score_per_period\("(.*?)"\)', content, re.DOTALL)
    assert rule_match is not None
    assert rule_match.group(1) == "7D"

def test_protocol_v1_26_4_tie_break_warning():
    path = Path("reports/research/preregistered_signal_validation_protocol_v1_26_4.json")
    if not path.exists():
        pytest.skip("V1.26.4 protocol not yet generated")
        
    with open(path) as f:
        protocol = json.load(f)
        
    defn = protocol["locked_filter_definition"]
    assert defn["tie_break_explicit"] is False
    assert "warning" in defn["tie_break_warning"].lower()

def test_completeness_audit_v1_26_4_status():
    path = Path("reports/research/preregistered_protocol_completeness_audit_v1_26_4.json")
    if not path.exists():
        pytest.skip("V1.26.4 audit not yet generated")
        
    with open(path) as f:
        audit = json.load(f)
        
    assert audit["status"] == "PREREGISTRATION_PROTOCOL_COMPLETE_WITH_TIE_BREAK_WARNING"
