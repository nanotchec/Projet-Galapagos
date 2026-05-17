"""Tests for Galapagos V1.17 - Recent Regime Failure Analysis."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from galapagos.research.failure_analysis.cost_failure import run_cost_analysis
from galapagos.research.failure_analysis.feature_drift import run_feature_drift_analysis
from galapagos.research.failure_analysis.recommendation_engine import run_recommendation_engine

ROOT = Path(__file__).parent.parent


def test_feature_drift_detection(tmp_path):
    """Test that feature drift correctly identifies significant drift."""
    # Create mock dataset
    dates = pd.date_range("2024-01-01", "2026-12-31", freq="D")
    df = pd.DataFrame({"timestamp": dates})
    df["year"] = df["timestamp"].dt.year
    
    # Stable feature
    df["stable_feat"] = np.random.normal(0, 1, len(df))
    
    # Drifting feature
    df["drift_feat"] = np.random.normal(0, 1, len(df))
    df.loc[df["year"] == 2026, "drift_feat"] += 5.0  # Large shift
    
    res = run_feature_drift_analysis(df, "v1.17", str(tmp_path))
    assert res["significant_drifts"] >= 1
    assert "drift_feat" in res["drift_details"]
    assert "stable_feat" not in res["drift_details"]


def test_cost_failure_sensitivity(tmp_path):
    """Test that cost failure analysis calculates sensitivities correctly."""
    dates = pd.date_range("2024-01-01", "2026-01-10", freq="D")
    df = pd.DataFrame({"timestamp": dates})
    df["year"] = df["timestamp"].dt.year
    
    # Mean gross return of 0.005
    df["forward_return_12bar"] = 0.005
    
    res = run_cost_analysis(df, "v1.17", str(tmp_path))
    
    # Base cost is 0.003
    # Net return should be 0.002
    assert "2026" in res["cost_analysis"]
    data = res["cost_analysis"]["2026"]
    assert abs(data["gross_forward_return"] - 0.005) < 1e-6
    assert abs(data["base_cost_adjusted_return"] - 0.002) < 1e-6


def test_recommendation_engine_verdict(tmp_path):
    """Test that recommendation engine synthesizes verdicts properly."""
    verdicts = {
        "data_gap_analysis": "INTRABAR_DATA_PRIORITY",
        "feature_drift": "FEATURE_DRIFT_LOW"
    }
    
    res = run_recommendation_engine(verdicts, "v1.17", str(tmp_path))
    assert res["primary_recommendation"] == "B. Add intrabar data first"
    assert "G. Do not activate LLM reviewer" in res["do_not_do_next"]


def test_no_codex_cli_v1_17():
    """Confirm no Codex CLI calls are wired in the codebase."""
    import subprocess
    cmd = (
        "grep -rE 'subprocess.*codex|codex.*subprocess' scripts/ src/galapagos/research/failure_analysis/"
        " --include='*.py' -l 2>/dev/null || true"
    )
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, shell=True)
    codex_files = [f for f in result.stdout.strip().split("\n") if f]
    assert codex_files == [], f"Unexpected active Codex CLI subprocess: {codex_files}"


def test_no_holdout_execution_v1_17():
    """Confirm holdout is not triggered in scripts."""
    import subprocess
    cmd = (
        "grep -rE 'run_holdout' scripts/ src/galapagos/research/failure_analysis/"
        " --include='*.py' -l 2>/dev/null || true"
    )
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, shell=True)
    holdout_files = [f for f in result.stdout.strip().split("\n") if f]
    assert holdout_files == [], f"Unexpected holdout execution: {holdout_files}"


def test_project_state_json_version_v1_17():
    """PROJECT_STATE.json must indicate V1.17 or a later research release."""
    state = json.loads((ROOT / "reports/PROJECT_STATE.json").read_text())
    assert state["version"].startswith("V1.")
    assert state.get("strategy_reviewer_ready") is False
    assert state.get("release_ready_for_external_review") is True
    assert state.get("real_orders_possible") is False or state.get("no_real_trading") is True
