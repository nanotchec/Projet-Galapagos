"""Unit tests for Galapagos V1.20.1 lineage and consistency."""
from __future__ import annotations

import json

import pandas as pd
from scripts.validate_intrabar_v1_20_reports import validate_reports
from src.galapagos.research.intrabar.data_lineage import inspect_intrabar_lineage


def test_lineage_detects_missing_file():
    res = inspect_intrabar_lineage("non_existent.parquet")
    assert res["status"] == "error"
    assert res["lineage_status"] == "INTRABAR_FILE_MISSING"

def test_lineage_reads_metadata(tmp_path):
    p = tmp_path / "test.parquet"
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(["2026-01-01", "2026-01-02"]),
        "open": [1, 2], "high": [2, 3], "low": [0, 1], "close": [1, 2], "volume": [10, 20]
    })
    df.to_parquet(p)
    
    res = inspect_intrabar_lineage(str(p))
    assert res["status"] == "success"
    assert res["rows"] == 2
    assert "2026-01-01" in res["first_timestamp"]

def test_consistency_check_fails_on_mismatch(tmp_path):
    # Mock reports dir
    reports_dir = tmp_path / "research"
    reports_dir.mkdir(parents=True)
    
    v = "v1_20_1"
    
    with open(reports_dir / f"intrabar_history_download_{v}.json", "w") as f:
        json.dump({"status": "dry_run"}, f)
    with open(reports_dir / f"intrabar_data_quality_{v}.json", "w") as f:
        json.dump({"status": "OK", "rows": 100, "start_time": "2026-01-01T00:00:00"}, f)
    with open(reports_dir / f"intrabar_data_lineage_{v}.json", "w") as f:
        json.dump({"rows": 200, "first_timestamp": "2026-01-01T00:00:00"}, f) # Mismatch rows
    with open(reports_dir / f"trade_ledger_intrabar_eval_{v}.json", "w") as f:
        json.dump({"intrabar_metadata": {"rows": 200}, "policy_metrics": {}}, f)
    
    res = validate_reports("v1.20.1", reports_dir=reports_dir)
    assert res["status"] == "INTRABAR_REPORTS_INCONSISTENT"
    assert any("Row mismatch" in iss for iss in res["issues"])
    assert any("Download report claims dry_run" in iss for iss in res["issues"])

def test_no_codex_no_holdout():
    """Security smoke test: confirm no active Codex CLI calls in scripts."""
    import subprocess
    # Check if scripts contain actual subprocess calls to codex
    cmd = "grep -rE 'subprocess.*codex|codex.*subprocess' scripts/ src/galapagos/research/ || true"
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    assert "subprocess" not in res.stdout
