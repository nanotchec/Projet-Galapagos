import pytest
import json
from pathlib import Path

def test_hardened_source_audit_status():
    path = Path("reports/research/frozen_filter_definition_v1_26_5.json")
    if not path.exists():
        pytest.skip("V1.26.5 audit not yet generated")
        
    with open(path) as f:
        defn = json.load(f)
        
    assert defn["source_extraction_status"] == "SOURCE_MATCHED_CODE_AND_REPORTS_STRICT"
    checks = defn["source_match_checks"]
    assert checks["sweep_rule_family_frequency"] is True
    assert checks["sweep_causal_true"] is True
    assert checks["selected_count_consistent"] is True
    assert checks["code_score_column_matched"] is True

def test_strict_completeness_audit():
    path = Path("reports/research/preregistered_protocol_completeness_audit_v1_26_5.json")
    if not path.exists():
        pytest.skip("V1.26.5 audit not yet generated")
        
    with open(path) as f:
        audit = json.load(f)
        
    assert audit["status"] == "PREREGISTRATION_PROTOCOL_COMPLETE_WITH_TIE_BREAK_WARNING"
    checks = audit["audit_checks"]
    assert checks["uses_future_returns_false"] is True
    assert checks["uses_realized_pnl_false"] is True
    assert checks["no_real_trading_true"] is True

def test_protocol_upgrade_reason():
    path = Path("reports/research/preregistered_signal_validation_protocol_v1_26_5.json")
    if not path.exists():
        pytest.skip("V1.26.5 protocol not yet generated")
        
    with open(path) as f:
        protocol = json.load(f)
        
    assert protocol["protocol_upgrade_reason"] == "strict_source_audit_hardening"
