from __future__ import annotations

import pandas as pd

from galapagos.research.intrabar.coverage_planner import plan_coverage
from galapagos.research.intrabar.data_quality import audit_intrabar_quality


def test_coverage_planner_logic(tmp_path):
    """Verify coverage planner calculations."""
    preds_path = tmp_path / "preds.parquet"
    # Create signals over a year
    dates = pd.date_range("2025-01-01", "2026-01-01", freq="4h")
    df = pd.DataFrame({"timestamp": dates})
    df.to_parquet(preds_path)
    
    ib_path = tmp_path / "ib.parquet"
    # Create intrabar for the last 30 days
    ib_dates = pd.date_range("2025-12-01", "2026-01-01", freq="5min")
    ib_df = pd.DataFrame({
        "timestamp": ib_dates,
        "open": 100, "high": 101, "low": 99, "close": 100, "volume": 10
    })
    ib_df.to_parquet(ib_path)
    
    result = plan_coverage(str(preds_path), str(ib_path), "v1.20-test")
    
    assert result["version"] == "v1.20-test"
    assert result["current_state"]["covered_candidates"] > 0
    assert result["plan"]["total_candidates"] == len(dates)
    assert "20%" in result["plan"]["targets"]

def test_data_quality_gap_detection(tmp_path):
    """Verify that gaps are detected."""
    ib_path = tmp_path / "ib_gaps.parquet"
    dates = pd.to_datetime([
        "2026-01-01 00:00:00",
        "2026-01-01 00:10:00"
    ])  # Gap of 10m instead of 5m
    df = pd.DataFrame({
        "timestamp": dates,
        "open": 100, "high": 101, "low": 99, "close": 100, "volume": 10
    })
    df.to_parquet(ib_path)
    
    result = audit_intrabar_quality(str(ib_path), "5min")
    assert result["status"] == "INTRABAR_DATA_HAS_GAPS"
    assert result["gaps_count"] == 1

def test_data_quality_ohlc_invalid(tmp_path):
    """Verify that invalid OHLC is detected."""
    ib_path = tmp_path / "ib_invalid.parquet"
    df = pd.DataFrame({
        "timestamp": [pd.Timestamp("2026-01-01")],
        "open": 100, "high": 90, # High < Open
        "low": 99, "close": 100, "volume": 10
    })
    df.to_parquet(ib_path)
    
    result = audit_intrabar_quality(str(ib_path))
    assert result["status"] == "INTRABAR_DATA_INVALID"
    assert result["ohlc_valid"] is False

def test_dry_run_no_network_scripts():
    """Verify scripts dry-run works without network."""
    import subprocess
    import sys
    
    # Coverage planner doesn't hit network anyway but we test its presence
    # Actually extend_history dry-run is more important
    cmd = [sys.executable, "scripts/extend_intrabar_history.py", "--dry-run", "--days", "10"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "dry_run" in res.stdout or "Download report" in res.stdout
