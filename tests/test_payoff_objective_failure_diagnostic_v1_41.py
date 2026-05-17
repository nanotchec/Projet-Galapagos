from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PREDICTIONS = ROOT / "data/gold/ml_predictions/BTC/4h/ml_predictions_v1_16_3.parquet"
DATASET = ROOT / "data/gold/research_dataset/BTC/4h/research_dataset_with_alpha_scores.parquet"
INTRABAR = ROOT / "data/silver/intrabar/binance/BTCUSDT/5m/history_5m_v1_22.parquet"
PAYOFF_SUMMARY = ROOT / "reports/research/payoff_objective_research_summary_v1_40_1.json"
PAYOFF_WALK_FORWARD = ROOT / "reports/research/payoff_objective_walk_forward_eval_v1_40_1.json"
PAYOFF_BASELINE = ROOT / "reports/research/payoff_objective_baseline_comparison_v1_40_1.json"
DIAGNOSTIC_SUMMARY = ROOT / "reports/research/ev_degradation_diagnostic_summary_v1_39.json"
CANONICAL_SUMMARY = ROOT / "reports/research/canonical_universe_summary_v1_37_2.json"


def _load_script(path: Path, module_name: str):
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_run_script():
    return _load_script(ROOT / "scripts" / "run_payoff_objective_failure_diagnostic.py", "run_payoff_objective_failure_diagnostic")


def _load_validator_script():
    return _load_script(
        ROOT / "scripts" / "validate_payoff_objective_failure_diagnostic_reports.py",
        "validate_payoff_objective_failure_diagnostic_reports",
    )


@pytest.fixture(scope="module")
def v141_workspace(tmp_path_factory: pytest.TempPathFactory) -> Path:
    workspace = tmp_path_factory.mktemp("v141_workspace")
    run_script = _load_run_script()
    old_cwd = Path.cwd()
    os.chdir(workspace)
    try:
        run_script.run_diagnostic(
            predictions=str(PREDICTIONS),
            dataset=str(DATASET),
            intrabar=str(INTRABAR),
            payoff_summary=str(PAYOFF_SUMMARY),
            payoff_walk_forward=str(PAYOFF_WALK_FORWARD),
            payoff_baseline=str(PAYOFF_BASELINE),
            canonical_summary=str(CANONICAL_SUMMARY),
            diagnostic_summary=str(DIAGNOSTIC_SUMMARY),
            version="v1.41",
        )
    finally:
        os.chdir(old_cwd)
    return workspace


def _validate_in_workspace(workspace: Path) -> dict:
    validator = _load_validator_script()
    old_cwd = Path.cwd()
    os.chdir(workspace)
    try:
        return validator.validate_payoff_objective_failure_diagnostic_reports("v1.41")
    finally:
        os.chdir(old_cwd)


def _copy_reports_tree(source_workspace: Path, target_workspace: Path) -> None:
    shutil.copytree(source_workspace / "reports", target_workspace / "reports")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_v141_summary_consistency_and_rebuild(v141_workspace: Path) -> None:
    summary = _load_json(v141_workspace / "reports/research/payoff_objective_failure_diagnostic_summary_v1_41.json")
    consistency = _load_json(v141_workspace / "reports/research/payoff_objective_failure_consistency_check_v1_41.json")
    rebuild = _load_json(v141_workspace / "reports/research/payoff_candidate_rebuild_v1_41.json")
    state = _load_json(v141_workspace / "reports/PROJECT_STATE.json")
    metrics = _load_json(v141_workspace / "reports/current/latest_metrics.json")

    assert summary["version"] == "V1.41"
    assert summary["payoff_objective_base_version"] == "V1.40.1"
    assert summary["diagnostic_base"] == "V1.39"
    assert summary["canonical_base_version"] == "V1.37.2"
    assert summary["research_base_version"] == "V1.38.4"
    assert summary["candidate"] == "asymmetric_loss_weighted_classifier"
    assert summary["candidate_rebuild_status"] == "PAYOFF_OBJECTIVE_CANDIDATE_REBUILD_MATCH"
    assert summary["metric_match_v1_40_1"] is True
    assert summary["downside_match_v1_40_1"] is True
    assert summary["best_candidate_2026_metric"] == pytest.approx(-0.004918998589848299)
    assert summary["best_candidate_downside_metric"] == pytest.approx(0.5385878489326765)
    assert summary["release_ready_for_external_review"] is True
    assert summary["strategy_reviewer_ready"] is False
    assert summary["paper_live_ready"] is False
    assert summary["preregistration_ready"] is False
    assert summary["money_deployment_ready"] is False
    assert summary["consistency_check_status"] == "PAYOFF_OBJECTIVE_FAILURE_DIAGNOSTIC_REPORTS_CONSISTENT_DIAGNOSTIC_ONLY"
    assert summary["status_field_policy"] == "REMOVED"
    assert summary["status_field_present"] is False
    assert summary["status_field_matches_consistency_check_status"] is True
    assert summary["ambiguous_ready_for_reviewer_removed"] is True
    assert consistency["consistency_check_status"] == "PAYOFF_OBJECTIVE_FAILURE_DIAGNOSTIC_REPORTS_CONSISTENT_DIAGNOSTIC_ONLY"
    assert "status" not in consistency
    assert consistency["status_field_present"] is False
    assert rebuild["rebuild_status"] == "PAYOFF_OBJECTIVE_CANDIDATE_REBUILD_MATCH"
    assert rebuild["metric_match_v1_40_1"] is True
    assert rebuild["downside_match_v1_40_1"] is True
    assert "ready_for_reviewer" not in state
    assert "ready_for_reviewer" not in metrics
    assert state["overfit_guard_status"] == "PAYOFF_OBJECTIVE_OVERFIT_RISK_MODERATE"
    assert metrics["overfit_guard_status"] == "PAYOFF_OBJECTIVE_OVERFIT_RISK_MODERATE"

    result = _validate_in_workspace(v141_workspace)
    assert result["status"] == "PAYOFF_OBJECTIVE_FAILURE_DIAGNOSTIC_REPORTS_CONSISTENT_DIAGNOSTIC_ONLY"
    assert result["issues"] == []


def test_validator_rejects_wrong_base_version(v141_workspace: Path, tmp_path: Path) -> None:
    _copy_reports_tree(v141_workspace, tmp_path)
    summary_path = tmp_path / "reports/research/payoff_objective_failure_diagnostic_summary_v1_41.json"
    summary = _load_json(summary_path)
    summary["payoff_objective_base_version"] = "V1.40"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    result = _validate_in_workspace(tmp_path)
    assert result["status"] == "PAYOFF_OBJECTIVE_FAILURE_DIAGNOSTIC_REPORTS_INCONSISTENT"
    assert any("payoff_objective_base_version" in issue for issue in result["issues"])


@pytest.mark.parametrize(
    ("field", "value", "fragment"),
    [
        ("candidate", "filter_ev_gt_0", "candidate"),
        ("evidence_classification", "EXPLORATORY_ONLY", "evidence_classification"),
        ("no_new_filter", False, "no_new_filter"),
        ("no_strategy_validated", False, "no_strategy_validated"),
        ("holdout_executed", True, "holdout_executed"),
        ("codex_cli_called", True, "codex_cli_called"),
        ("paper_live_ready", True, "paper_live_ready"),
        ("strategy_reviewer_ready", True, "strategy_reviewer_ready"),
    ],
)
def test_validator_rejects_core_semantic_mutations(
    v141_workspace: Path, tmp_path: Path, field: str, value: object, fragment: str
) -> None:
    _copy_reports_tree(v141_workspace, tmp_path)
    summary_path = tmp_path / "reports/research/payoff_objective_failure_diagnostic_summary_v1_41.json"
    summary = _load_json(summary_path)
    summary[field] = value
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    result = _validate_in_workspace(tmp_path)
    assert result["status"] == "PAYOFF_OBJECTIVE_FAILURE_DIAGNOSTIC_REPORTS_INCONSISTENT"
    assert any(fragment in issue for issue in result["issues"])


def test_validator_rejects_legacy_status_field(v141_workspace: Path, tmp_path: Path) -> None:
    _copy_reports_tree(v141_workspace, tmp_path)
    consistency_path = tmp_path / "reports/research/payoff_objective_failure_consistency_check_v1_41.json"
    consistency = _load_json(consistency_path)
    consistency["status"] = "PAYOFF_OBJECTIVE_FAILURE_DIAGNOSTIC_REPORTS_CONSISTENT_DIAGNOSTIC_ONLY"
    consistency_path.write_text(json.dumps(consistency, indent=2, ensure_ascii=False), encoding="utf-8")

    result = _validate_in_workspace(tmp_path)
    assert result["status"] == "PAYOFF_OBJECTIVE_FAILURE_DIAGNOSTIC_REPORTS_INCONSISTENT"
    assert any("legacy status" in issue for issue in result["issues"])


def test_validator_rejects_status_field_present_true(v141_workspace: Path, tmp_path: Path) -> None:
    _copy_reports_tree(v141_workspace, tmp_path)
    consistency_path = tmp_path / "reports/research/payoff_objective_failure_consistency_check_v1_41.json"
    consistency = _load_json(consistency_path)
    consistency["status_field_present"] = True
    consistency_path.write_text(json.dumps(consistency, indent=2, ensure_ascii=False), encoding="utf-8")

    result = _validate_in_workspace(tmp_path)
    assert result["status"] == "PAYOFF_OBJECTIVE_FAILURE_DIAGNOSTIC_REPORTS_INCONSISTENT"
    assert any("status_field_present" in issue for issue in result["issues"])


def test_validator_rejects_ready_for_reviewer_in_state_and_metrics(v141_workspace: Path, tmp_path: Path) -> None:
    _copy_reports_tree(v141_workspace, tmp_path)
    state_path = tmp_path / "reports/PROJECT_STATE.json"
    metrics_path = tmp_path / "reports/current/latest_metrics.json"
    state = _load_json(state_path)
    metrics = _load_json(metrics_path)
    state["ready_for_reviewer"] = False
    metrics["ready_for_reviewer"] = False
    state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    metrics_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")

    result = _validate_in_workspace(tmp_path)
    assert result["status"] == "PAYOFF_OBJECTIVE_FAILURE_DIAGNOSTIC_REPORTS_INCONSISTENT"
    assert any("ready_for_reviewer" in issue for issue in result["issues"])


def test_validator_rejects_changed_best_filter_metrics(v141_workspace: Path, tmp_path: Path) -> None:
    _copy_reports_tree(v141_workspace, tmp_path)
    summary_path = tmp_path / "reports/research/payoff_objective_failure_diagnostic_summary_v1_41.json"
    summary = _load_json(summary_path)
    summary["best_candidate_2026_metric"] = 0.0
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    result = _validate_in_workspace(tmp_path)
    assert result["status"] == "PAYOFF_OBJECTIVE_FAILURE_DIAGNOSTIC_REPORTS_INCONSISTENT"
    assert any("best_candidate_2026_metric" in issue or "metric" in issue for issue in result["issues"])
