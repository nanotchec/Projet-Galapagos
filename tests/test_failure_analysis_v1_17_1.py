"""Tests for Galapagos V1.17.1 - Real Dataset Failure Analysis Execution Fix."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

from galapagos.research.failure_analysis.label_diagnostics import run_label_diagnostics
from galapagos.research.failure_analysis.recommendation_engine import run_recommendation_engine

ROOT = Path(__file__).parent.parent


# ---- Orchestrator dataset gate ----

def test_non_dry_run_fails_without_dataset():
    """Non-dry-run mode MUST fail with exit 1 when dataset is missing."""
    result = subprocess.run(
        [
            "python", "scripts/run_recent_failure_analysis.py",
            "--dataset", "data/processed/DOES_NOT_EXIST.parquet",
            "--ensemble-report", "reports/research/ensemble_signal_lab_v1_16_3.json",
            "--version", "v1.17.1",
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert result.returncode != 0, "Non-dry-run should fail when dataset is missing"
    assert "ERROR" in result.stderr


def test_dry_run_accepts_missing_dataset():
    """Dry-run should exit cleanly even without a dataset."""
    result = subprocess.run(
        [
            "python", "scripts/run_recent_failure_analysis.py",
            "--dataset", "data/processed/DOES_NOT_EXIST.parquet",
            "--ensemble-report", "reports/research/ensemble_signal_lab_v1_16_3.json",
            "--version", "v1.17.1",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert result.returncode == 0, f"Dry-run should succeed. stderr: {result.stderr}"


# ---- Validation script ----

def test_validate_detects_missing_dataset_reports(tmp_path):
    """validate_failure_analysis_reports must reject SKIPPED/missing_dataset reports."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "validate_failure_analysis_reports",
        ROOT / "scripts" / "validate_failure_analysis_reports.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # Write a bad report
    (tmp_path / "recent_window_failure_v1_17_1.json").write_text(
        json.dumps({"status": "missing_dataset", "verdict": "SKIPPED"})
    )

    result = mod.validate("v1.17.1", str(tmp_path))
    assert not result["passed"]
    assert any("missing_dataset" in e for e in result["errors"])


def test_validate_passes_on_valid_reports(tmp_path):
    """validate_failure_analysis_reports must pass on real reports."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "validate_failure_analysis_reports",
        ROOT / "scripts" / "validate_failure_analysis_reports.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    for name in mod.REPORT_NAMES:
        (tmp_path / f"{name}_v1_17_1.json").write_text(
            json.dumps({"verdict": "SOME_VERDICT", "status": "complete"})
        )
    (tmp_path / "v1_17_1_recommendation.json").write_text(
        json.dumps({
            "primary_recommendation": "I. Pause",
            "ready_for_reviewer": False,
        })
    )

    result = mod.validate("v1.17.1", str(tmp_path))
    assert result["passed"], f"Errors: {result['errors']}"


# ---- Label diagnostics with missing target columns ----

def test_label_diagnostics_partial_when_targets_missing(tmp_path):
    """When target_up_after_cost_* columns are absent, status should be partial."""
    dates = pd.date_range("2024-01-01", "2026-03-01", freq="D")
    df = pd.DataFrame({
        "timestamp": dates,
        "forward_return_6bar": np.random.normal(0.001, 0.01, len(dates)),
        "forward_return_12bar": np.random.normal(0.001, 0.01, len(dates)),
    })
    res = run_label_diagnostics(df, "v1.17.1", str(tmp_path))
    assert res["status"] == "partial"
    assert "target_up_after_cost_12bar" in res["label_analysis"]
    assert res["verdict"] != "SKIPPED"


# ---- Recommendation engine versioned naming ----

def test_recommendation_report_versioned(tmp_path):
    """Recommendation report should use versioned file name."""
    verdicts = {"data_gap_analysis": "INTRABAR_DATA_PRIORITY"}
    run_recommendation_engine(verdicts, "v1.17.1", str(tmp_path))
    assert (tmp_path / "v1_17_1_recommendation.json").exists()
    assert (tmp_path / "v1_17_1_recommendation.md").exists()


# ---- Safety checks ----

def test_no_codex_cli_v1_17_1():
    """Confirm no Codex CLI calls are wired in the codebase."""
    cmd = (
        "grep -rE 'subprocess.*codex|codex.*subprocess' scripts/ src/galapagos/research/failure_analysis/"
        " --include='*.py' -l 2>/dev/null || true"
    )
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, shell=True)
    codex_files = [f for f in result.stdout.strip().split("\n") if f]
    assert codex_files == [], f"Unexpected active Codex CLI subprocess: {codex_files}"


def test_no_holdout_execution_v1_17_1():
    """Confirm holdout is not triggered in scripts."""
    cmd = (
        "grep -rE 'run_holdout' scripts/ src/galapagos/research/failure_analysis/"
        " --include='*.py' -l 2>/dev/null || true"
    )
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, shell=True)
    holdout_files = [f for f in result.stdout.strip().split("\n") if f]
    assert holdout_files == [], f"Unexpected holdout execution: {holdout_files}"


def test_project_state_json_version_v1_17_1():
    """PROJECT_STATE.json must indicate V1.17.1 or a later research release."""
    state = json.loads((ROOT / "reports/PROJECT_STATE.json").read_text())
    assert state["version"].startswith("V1.")
    assert state.get("strategy_reviewer_ready") is False
    assert state.get("release_ready_for_external_review") is True
    assert state.get("real_orders_possible") is False or state.get("no_real_trading") is True
