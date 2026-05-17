import pytest
import pandas as pd
from pathlib import Path
from audit_protocol_immutability import calculate_protocol_hash, run_protocol_immutability_audit
from galapagos.research.paper_forward.mock_audit import run_mock_audit
from galapagos.research.paper_forward.validation_engine import compute_realized_metrics

def test_protocol_immutability_detects_mutation(tmp_path):
    p = tmp_path / "proto.json"
    p.write_text('{"locked": true}')
    initial_hash = calculate_protocol_hash(str(p))
    
    # Mutate
    p.write_text('{"locked": false}')
    res = run_protocol_immutability_audit(str(p), initial_hash)
    assert res["protocol_mutated_during_run"] is True
    assert res["status"] == "PROTOCOL_MUTATION_DETECTED"

def test_mock_audit_detects_placeholder(tmp_path):
    # Test on a temporary file
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "engine.py").write_text('profit_factor = 1.0 # Placeholder')
    
    res = run_mock_audit(str(pkg))
    assert res["mock_components_present"] is True
    assert any("profit_factor = 1.0" in hit["hit"] for hit in res["hits"])

def test_compute_realized_metrics_no_placeholders():
    # Test on trades without PnL
    df = pd.DataFrame({"id": [1, 2]})
    res = compute_realized_metrics(df)
    assert res["profit_factor"] is None
    assert res["top_10_trades_contribution"] is None
    assert res["status"] == "METRICS_NOT_AVAILABLE"

def test_compute_realized_metrics_with_data():
    df = pd.DataFrame({"mean_net_pnl_after_cost_pct": [0.1, -0.05, 0.2]})
    res = compute_realized_metrics(df)
    assert res["mean_net_pnl_after_cost_pct"] == pytest.approx(0.08333, abs=1e-4)
    # Pos = 0.3, Neg = 0.05 => PF = 6.0
    assert res["profit_factor"] == pytest.approx(6.0)
