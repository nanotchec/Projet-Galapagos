"""Unit tests for Galapagos V1.21."""
from __future__ import annotations

import json
from pathlib import Path


def test_v1_21_intrabar_filename():
    """V1.21 must use history_5m_v1_21.parquet"""
    # Check if the file was created during execution
    path = Path("data/silver/intrabar/binance/BTCUSDT/5m/history_5m_v1_21.parquet")
    assert path.exists()

def test_v1_21_coverage_reached():
    """V1.21 must have reached 20% target in reports."""
    path = Path("reports/research/trade_ledger_intrabar_eval_v1_21.json")
    assert path.exists()
    with open(path) as f:
        data = json.load(f)
    assert data["target_reached"] is True
    assert data["evaluated_ratio"] >= 0.20

def test_v1_21_safety_constraints():
    """V1.21 must maintain safety constraints."""
    path = Path("reports/PROJECT_STATE.json")
    with open(path) as f:
        data = json.load(f)
    assert data.get("strategy_reviewer_ready") is False
    assert data.get("release_ready_for_external_review") is True
    assert data["holdout_executed"] is False
    assert data["codex_cli_called"] is False
    assert data["real_trading_possible"] is False

def test_v1_21_consistency():
    """V1.21 reports must be consistent."""
    path = Path("reports/research/intrabar_v1_21_consistency_check.json")
    assert path.exists()
    with open(path) as f:
        data = json.load(f)
    assert data["status"] == "INTRABAR_REPORTS_CONSISTENT"
