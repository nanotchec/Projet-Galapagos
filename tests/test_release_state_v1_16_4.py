"""Tests for Galapagos V1.16.4 - Final Release State Consistency Fix."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent


def test_project_state_json_version_v1_16_4():
    """PROJECT_STATE.json must indicate a V1 research release."""
    state = json.loads((ROOT / "reports/PROJECT_STATE.json").read_text())
    assert state["version"].startswith("V1.")


def test_project_state_ensemble_verdict():
    """PROJECT_STATE.json must carry a conservative research verdict."""
    state = json.loads((ROOT / "reports/PROJECT_STATE.json").read_text())
    assert state.get("scientific_verdict") or state.get("ensemble_verdict")
    assert state.get("strategy_reviewer_ready") is False


def test_project_state_no_real_trading():
    """PROJECT_STATE.json must confirm no real trading is possible."""
    state = json.loads((ROOT / "reports/PROJECT_STATE.json").read_text())
    assert state.get("real_orders_possible") is False or state.get("no_real_trading") is True
    assert state.get("codex_cli") in {"non appele", "not_called"}
    assert state.get("holdout_status") in {"non execute", "not_executed_locked"}


def test_latest_metrics_version_v1_16_4():
    """latest_metrics.json must indicate a V1 research release."""
    metrics = json.loads((ROOT / "reports/current/latest_metrics.json").read_text())
    assert metrics["version"].lower().startswith("v1.")


def test_latest_metrics_not_ready():
    """latest_metrics.json must indicate not ready for reviewer."""
    metrics = json.loads((ROOT / "reports/current/latest_metrics.json").read_text())
    assert metrics.get("strategy_reviewer_ready") is False
    assert metrics.get("release_ready_for_external_review") is True
    assert metrics.get("real_trading_possible") is False or metrics.get("no_real_trading") is True


def test_release_report_consistency():
    """If release report exists, final_zip_created=True implies release_ready is coherent."""
    report_path = ROOT / "reports/release_zip_v1_16_4.json"
    if not report_path.exists():
        pytest.skip("release_zip_v1_16_4.json not yet generated")
    report = json.loads(report_path.read_text())
    # If final_zip_created is False, release cannot be ready
    if not report.get("final_zip_created", False):
        assert report.get("release_ready_for_external_review", True) is False, (
            "release_ready must be False when final_zip_created is False"
        )


def test_release_report_no_false_zip_created():
    """The definitive release report must have final_zip_created=True."""
    report_path = ROOT / "reports/release_zip_v1_16_4.json"
    if not report_path.exists():
        pytest.skip("release_zip_v1_16_4.json not yet generated")
    report = json.loads(report_path.read_text())
    assert report["final_zip_created"] is True


def test_no_codex_cli():
    """Confirm no active (unguarded) Codex CLI subprocess calls in research scripts."""
    import subprocess
    cmd = (
        "grep -rE 'subprocess.*codex|codex.*subprocess' scripts/"
        " --include='*.py' -l 2>/dev/null || true"
    )
    result2 = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, shell=True)
    codex_files = [f for f in result2.stdout.strip().split("\n") if f]
    assert codex_files == [], f"Unexpected active Codex CLI subprocess in scripts/: {codex_files}"


def test_no_holdout_execution():
    """Confirm holdout is not triggered in research scripts."""
    import subprocess
    result = subprocess.run(
        ["grep", "-r", "run_holdout", "scripts/", "--include=*.py", "-l"],
        capture_output=True, text=True, cwd=ROOT
    )
    holdout_files = [f for f in result.stdout.strip().split("\n") if f]
    assert holdout_files == [], f"Unexpected holdout execution in: {holdout_files}"
