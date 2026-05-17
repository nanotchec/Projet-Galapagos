import pytest
import pandas as pd
from pathlib import Path
from galapagos.research.paper_forward.mock_audit import run_mock_audit
from galapagos.research.paper_forward.validation_engine import run_paper_forward_validation

def test_mock_audit_ignores_self_reference(tmp_path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    # Create mock_audit.py containing forbidden strings
    (pkg / "mock_audit.py").write_text('forbidden = ["Mock", "Placeholder"]')
    
    res = run_mock_audit(str(pkg))
    assert res["status"] == "PAPER_FORWARD_SELF_REFERENCE_ONLY"
    assert res["mock_components_present"] is False
    assert len(res["self_reference_hits"]) > 0
    assert len(res["blocking_hits"]) == 0

def test_mock_audit_detects_real_blocking_hit(tmp_path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "mock_audit.py").write_text('forbidden = ["Mock"]')
    (pkg / "engine.py").write_text('profit_factor = 1.0 # Placeholder')
    
    res = run_mock_audit(str(pkg))
    assert res["status"] == "PAPER_FORWARD_MOCKS_DETECTED"
    assert res["mock_components_present"] is True
    assert len(res["blocking_hits"]) > 0

def test_validation_status_priority_filter_insufficient():
    protocol = {
        "candidate_filter": "low_frequency_strict_score",
        "locked_filter_definition": {"score_column": "score"} # Missing threshold
    }
    preds = pd.DataFrame({
        "timestamp": [pd.Timestamp("2026-05-07")],
        "score": [0.9]
    })
    
    # We need to simulate the orchestrator logic or check validation_engine direct return
    res = run_paper_forward_validation(protocol, {}, preds, pd.DataFrame(), pd.DataFrame())
    # The validation_engine itself returns FROZEN_FILTER_DEFINITION_INSUFFICIENT if threshold missing
    assert res["reason"] == "FROZEN_FILTER_DEFINITION_INSUFFICIENT"
    assert res["criteria_status"] == "NOT_EVALUATED_FILTER_NOT_RECONSTRUCTABLE"
