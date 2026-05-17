from __future__ import annotations

import pandas as pd

from galapagos.research.trade_ledger.comparison import compare_policies
from galapagos.research.trade_ledger.metrics import calculate_policy_metrics
from galapagos.research.trade_ledger.schema import TradeSide, TradeSimulationResult


def test_evaluated_ratio_calculation():
    """Verify that evaluated_ratio is calculated correctly."""
    results = [
        TradeSimulationResult(
            candidate_id="1",
            signal_time=pd.Timestamp("2026-01-01", tz="UTC"),
            entry_time=pd.Timestamp("2026-01-01", tz="UTC"),
            side=TradeSide.LONG,
            entry_price=100.0,
            exit_price=105.0,
            exit_time=pd.Timestamp("2026-01-01", tz="UTC"),
            exit_reason="tp",
            pnl_pct=0.05,
            pnl_after_cost_pct=0.047,
            simulation_status="complete"
        ),
        TradeSimulationResult(
            candidate_id="2",
            signal_time=pd.Timestamp("2026-01-02", tz="UTC"),
            entry_time=pd.Timestamp("2026-01-02", tz="UTC"),
            side=TradeSide.LONG,
            entry_price=100.0,
            exit_price=None,
            exit_time=pd.Timestamp("2026-01-02", tz="UTC"),
            exit_reason="missing",
            pnl_pct=0.0,
            pnl_after_cost_pct=-0.003,
            simulation_status="missing_data"
        )
    ]
    
    metrics = calculate_policy_metrics(results)
    assert metrics["evaluated_ratio"] == 0.5
    assert metrics["intrabar_sample_limited"] is False  # 0.5 >= 0.2

def test_verdict_sample_too_short():
    """Verify that verdict is TRADE_LEDGER_INTRABAR_SAMPLE_TOO_SHORT if coverage is low."""
    policy_metrics = {
        "policy_A": {
            "evaluated_ratio": 0.1,
            "mean_pnl_after_cost_pct": 0.05,
            "median_pnl_after_cost_pct": 0.01
        }
    }
    
    comparison = compare_policies(policy_metrics)
    assert comparison["verdict"] == "TRADE_LEDGER_INTRABAR_SAMPLE_TOO_SHORT"
    assert comparison["policy_comparison_valid"] is False
    assert comparison["best_policy"].startswith("observed_only_")

def test_median_pnl_negative_warning():
    """Verify that MEDIAN_PNL_NEGATIVE_ALL_POLICIES warning is added."""
    policy_metrics = {
        "policy_A": {
            "evaluated_ratio": 0.3,
            "mean_pnl_after_cost_pct": 0.001,
            "median_pnl_after_cost_pct": -0.001
        }
    }
    
    comparison = compare_policies(policy_metrics)
    assert "MEDIAN_PNL_NEGATIVE_ALL_POLICIES" in comparison["warnings"]
    assert comparison["all_median_negative"] is True

def test_dry_run_no_crash():
    """Verify that run_trade_ledger_intrabar_eval.py --dry-run doesn't crash without predictions."""
    import subprocess
    import sys
    
    cmd = [
        sys.executable,
        "scripts/run_trade_ledger_intrabar_eval.py",
        "--dry-run",
        "--version",
        "v1.19.2-test",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0
    assert "Dry-run complete" in result.stdout
