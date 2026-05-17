from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path

import pandas as pd
import pytest

from galapagos.research.payoff_aware_objective.target_builder import build_targets


ROOT = Path(__file__).resolve().parents[1]
PREDICTIONS = ROOT / "data/gold/ml_predictions/BTC/4h/ml_predictions_v1_16_3.parquet"
DATASET = ROOT / "data/gold/research_dataset/BTC/4h/research_dataset_with_alpha_scores.parquet"
INTRABAR = ROOT / "data/silver/intrabar/binance/BTCUSDT/5m/history_5m_v1_22.parquet"
DIAGNOSTIC_SUMMARY = ROOT / "reports/research/ev_degradation_diagnostic_summary_v1_39.json"
EV_SUMMARY = ROOT / "reports/research/ev_net_research_summary_v1_38_4.json"
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
    return _load_script(ROOT / "scripts" / "run_payoff_objective_research.py", "run_payoff_objective_research")


def _load_validator_script():
    return _load_script(
        ROOT / "scripts" / "validate_payoff_objective_reports.py",
        "validate_payoff_objective_reports",
    )


@pytest.fixture(scope="module")
def v140_workspace(tmp_path_factory: pytest.TempPathFactory) -> Path:
    workspace = tmp_path_factory.mktemp("v140_workspace")
    run_script = _load_run_script()
    old_cwd = Path.cwd()
    os.chdir(workspace)
    try:
        run_script.run_research(
            predictions=str(PREDICTIONS),
            dataset=str(DATASET),
            intrabar=str(INTRABAR),
            diagnostic_summary=str(DIAGNOSTIC_SUMMARY),
            ev_summary=str(EV_SUMMARY),
            canonical_summary=str(CANONICAL_SUMMARY),
            version="v1.40",
        )
    finally:
        os.chdir(old_cwd)
    return workspace


def _validate_in_workspace(workspace: Path) -> dict:
    validator = _load_validator_script()
    old_cwd = Path.cwd()
    os.chdir(workspace)
    try:
        return validator.validate_payoff_objective_reports("v1.40")
    finally:
        os.chdir(old_cwd)


def _copy_reports_tree(source_workspace: Path, target_workspace: Path) -> None:
    shutil.copytree(source_workspace / "reports", target_workspace / "reports")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_v140_reports_are_label_only_and_consistent(v140_workspace: Path) -> None:
    summary = _load_json(v140_workspace / "reports/research/payoff_objective_research_summary_v1_40.json")
    targets = _load_json(v140_workspace / "reports/research/payoff_objective_targets_v1_40.json")
    consistency = _load_json(v140_workspace / "reports/research/payoff_objective_consistency_check_v1_40.json")
    state = _load_json(v140_workspace / "reports/PROJECT_STATE.json")
    metrics = _load_json(v140_workspace / "reports/current/latest_metrics.json")

    assert summary["version"] == "V1.40"
    assert summary["diagnostic_base"] == "V1.39"
    assert summary["canonical_base_version"] == "V1.37.2"
    assert summary["research_base_version"] == "V1.38.4"
    assert summary["consistency_check_status"] == "PAYOFF_OBJECTIVE_REPORTS_CONSISTENT_EXPLORATORY_ONLY"
    assert summary["status_field_policy"] == "REMOVED"
    assert summary["status_field_present"] is False
    assert summary["release_ready_for_external_review"] is True
    assert summary["strategy_reviewer_ready"] is False
    assert summary["paper_live_ready"] is False
    assert summary["preregistration_ready"] is False
    assert summary["money_deployment_ready"] is False
    assert summary["evidence_classification"] == "EXPLORATORY_ONLY"
    assert summary["no_new_filter"] is True
    assert summary["no_strategy_validated"] is True
    assert summary["no_preregistration_yet"] is True
    assert summary["no_paper_live"] is True
    assert summary["no_real_trading"] is True
    assert "ready_for_reviewer" not in state
    assert "ready_for_reviewer" not in metrics
    assert consistency["consistency_check_status"] == "PAYOFF_OBJECTIVE_REPORTS_CONSISTENT_EXPLORATORY_ONLY"
    assert "status" not in consistency
    assert consistency["status_field_policy"] == "REMOVED"
    assert consistency["status_field_present"] is False
    assert targets["payoff_target_status"] == "PAYOFF_OBJECTIVE_TARGETS_DEFINED_LABEL_ONLY"
    assert targets["future_outcomes_used_only_as_training_labels"] is True
    assert targets["targets_not_available_at_decision_time"] is True
    assert targets["target_leakage_policy"] == "LABEL_ONLY_NOT_SELECTION_FEATURE"

    result = _validate_in_workspace(v140_workspace)
    assert result["status"] == "PAYOFF_OBJECTIVE_REPORTS_CONSISTENT_EXPLORATORY_ONLY"
    assert result["issues"] == []


def test_target_builder_marks_outcomes_label_only() -> None:
    frame = pd.DataFrame(
        {
            "forward_return_12bar": [0.01, -0.02],
            "cost_proxy": [0.001, 0.002],
            "ev_calibrated_proxy": [0.008, -0.010],
        }
    )
    labeled, report = build_targets(frame)
    assert len(labeled) == 2
    assert report["future_outcomes_used_only_as_training_labels"] is True
    assert report["targets_not_available_at_decision_time"] is True
    assert report["target_leakage_policy"] == "LABEL_ONLY_NOT_SELECTION_FEATURE"
    assert report["labels_only"] is True


def test_validator_rejects_legacy_status_field(v140_workspace: Path, tmp_path: Path) -> None:
    _copy_reports_tree(v140_workspace, tmp_path)
    consistency_path = tmp_path / "reports/research/payoff_objective_consistency_check_v1_40.json"
    consistency = _load_json(consistency_path)
    consistency["status"] = "PAYOFF_OBJECTIVE_REPORTS_CONSISTENT_EXPLORATORY_ONLY"
    consistency_path.write_text(json.dumps(consistency, indent=2, ensure_ascii=False), encoding="utf-8")

    result = _validate_in_workspace(tmp_path)
    assert result["status"] == "PAYOFF_OBJECTIVE_REPORTS_INCONSISTENT"
    assert any("legacy status" in issue for issue in result["issues"])


def test_validator_rejects_status_field_present_true(v140_workspace: Path, tmp_path: Path) -> None:
    _copy_reports_tree(v140_workspace, tmp_path)
    consistency_path = tmp_path / "reports/research/payoff_objective_consistency_check_v1_40.json"
    consistency = _load_json(consistency_path)
    consistency["status_field_present"] = True
    consistency_path.write_text(json.dumps(consistency, indent=2, ensure_ascii=False), encoding="utf-8")

    result = _validate_in_workspace(tmp_path)
    assert result["status"] == "PAYOFF_OBJECTIVE_REPORTS_INCONSISTENT"
    assert any("status_field_present" in issue for issue in result["issues"])


def test_validator_rejects_outcomes_used_as_selection_features(v140_workspace: Path, tmp_path: Path) -> None:
    _copy_reports_tree(v140_workspace, tmp_path)
    candidates_path = tmp_path / "reports/research/payoff_objective_candidates_v1_40.json"
    candidates = _load_json(candidates_path)
    candidates["candidates"][0]["feature_columns"].append("forward_return_12bar")
    candidates_path.write_text(json.dumps(candidates, indent=2, ensure_ascii=False), encoding="utf-8")

    result = _validate_in_workspace(tmp_path)
    assert result["status"] == "PAYOFF_OBJECTIVE_REPORTS_INCONSISTENT"
    assert any("Forbidden feature column" in issue for issue in result["issues"])


@pytest.mark.parametrize(
    ("field", "value", "expected_fragment"),
    [
        ("evidence_classification", "DIAGNOSTIC_ONLY", "evidence_classification"),
        ("no_new_filter", False, "no_new_filter"),
        ("no_strategy_validated", False, "no_strategy_validated"),
        ("paper_live_ready", True, "paper_live_ready"),
        ("holdout_executed", True, "holdout_executed"),
    ],
)
def test_validator_rejects_core_semantic_mutations(
    v140_workspace: Path, tmp_path: Path, field: str, value: object, expected_fragment: str
) -> None:
    _copy_reports_tree(v140_workspace, tmp_path)
    summary_path = tmp_path / "reports/research/payoff_objective_research_summary_v1_40.json"
    summary = _load_json(summary_path)
    summary[field] = value
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    result = _validate_in_workspace(tmp_path)
    assert result["status"] == "PAYOFF_OBJECTIVE_REPORTS_INCONSISTENT"
    assert any(expected_fragment in issue for issue in result["issues"])


def test_validator_rejects_ready_for_reviewer_in_state(v140_workspace: Path, tmp_path: Path) -> None:
    _copy_reports_tree(v140_workspace, tmp_path)
    state_path = tmp_path / "reports/PROJECT_STATE.json"
    state = _load_json(state_path)
    state["ready_for_reviewer"] = False
    state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

    result = _validate_in_workspace(tmp_path)
    assert result["status"] == "PAYOFF_OBJECTIVE_REPORTS_INCONSISTENT"
    assert any("ready_for_reviewer" in issue for issue in result["issues"])


def test_validator_rejects_ready_for_reviewer_in_metrics(v140_workspace: Path, tmp_path: Path) -> None:
    _copy_reports_tree(v140_workspace, tmp_path)
    metrics_path = tmp_path / "reports/current/latest_metrics.json"
    metrics = _load_json(metrics_path)
    metrics["ready_for_reviewer"] = False
    metrics_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")

    result = _validate_in_workspace(tmp_path)
    assert result["status"] == "PAYOFF_OBJECTIVE_REPORTS_INCONSISTENT"
    assert any("ready_for_reviewer" in issue for issue in result["issues"])
