"""Tests for intrabar foundation honesty and real signal support (V1.18.1)."""
from __future__ import annotations

import pandas as pd

from galapagos.research.intrabar.comparison import compare_simulations
from galapagos.research.intrabar.cost_model import evaluate_cost_stress


def test_cost_model_terminology():
    """Test that cost model uses 'range' instead of 'spread'."""
    df = pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=5, freq="5min"),
        "open": [50000.0] * 5,
        "high": [50100.0] * 5,
        "low": [49900.0] * 5,
        "close": [50000.0] * 5
    })
    res = evaluate_cost_stress(df)
    assert "mean_intrabar_range_pct" in res["details"]
    assert "mean_intrabar_spread_pct" not in res["details"]
    assert "note" in res
    assert "is not bid/ask spread" in res["note"].lower()


def test_comparison_honesty():
    """Test that comparison fails honestly if 4h results are missing."""
    df_intrabar = pd.DataFrame({"ambiguous": [False], "used_fallback": [False]})
    df_4h_empty = pd.DataFrame()
    
    res = compare_simulations(df_4h_empty, df_intrabar)
    assert res["verdict"] == "INTRABAR_COMPARISON_NOT_YET_VALID"
    assert res["reason"] == "missing_4h_reference_results"


def test_security_constraints():
    """Verify that no Codex CLI, no holdout, no real trading are mentioned in docs."""
    from pathlib import Path
    summary_path = Path("reports/current/latest_summary.md")
    content = summary_path.read_text()
    assert "Codex CLI** : Non appelé" in content
    assert "Holdout** : Non exécuté" in content
    assert "Trading Réel** : Désactivé" in content
