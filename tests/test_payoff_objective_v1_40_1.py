from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path

import pandas as pd
import pytest

from galapagos.research.payoff_aware_objective.objective_schema import build_walk_forward_split_integrity


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
    return _load_script(ROOT / "scripts" / "run_payoff_objective_research.py", "run_payoff_objective_research_v1401")


def _load_validator_script():
    return _load_script(ROOT / "scripts" / "validate_payoff_objective_reports.py", "validate_payoff_objective_reports_v1401")


@pytest.fixture(scope="module")
def v1401_workspace(tmp_path_factory: pytest.TempPathFactory) -> Path:
    workspace = tmp_path_factory.mktemp("v1401_workspace")
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
            version="v1.40.1",
        )
    finally:
        os.chdir(old_cwd)
    return workspace


def _validate_in_workspace(workspace: Path) -> dict:
    validator = _load_validator_script()
    old_cwd = Path.cwd()
    os.chdir(workspace)
    try:
        return validator.validate_payoff_objective_reports("v1.40.1")
    finally:
        os.chdir(old_cwd)


def _copy_reports_tree(source_workspace: Path, target_workspace: Path) -> None:
    shutil.copytree(source_workspace / "reports", target_workspace / "reports")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_v1401_split_integrity_and_consistency(v1401_workspace: Path) -> None:
    summary = _load_json(v1401_workspace / "reports/research/payoff_objective_research_summary_v1_40_1.json")
    split_integrity = _load_json(v1401_workspace / "reports/research/payoff_objective_split_integrity_v1_40_1.json")
    walk_forward = _load_json(v1401_workspace / "reports/research/payoff_objective_walk_forward_eval_v1_40_1.json")
    consistency = _load_json(v1401_workspace / "reports/research/payoff_objective_consistency_check_v1_40_1.json")
    state = _load_json(v1401_workspace / "reports/PROJECT_STATE.json")
    metrics = _load_json(v1401_workspace / "reports/current/latest_metrics.json")

    assert summary["version"] == "V1.40.1"
    assert summary["previous_base"] == "V1.40"
    assert summary["split_integrity_status"] == "PAYOFF_OBJECTIVE_SPLIT_INTEGRITY_PASSED"
    assert summary["invalid_split_count"] == 0
    assert summary["all_splits_temporally_valid"] is True
    assert summary["overfit_guard_status"] == "PAYOFF_OBJECTIVE_OVERFIT_RISK_MODERATE"
    assert "ready_for_reviewer" not in state
    assert "ready_for_reviewer" not in metrics
    assert "status" not in consistency
    assert consistency["consistency_check_status"] == "PAYOFF_OBJECTIVE_REPORTS_CONSISTENT_VALID_SPLITS_EXPLORATORY_ONLY"
    assert consistency["status_field_policy"] == "REMOVED"
    assert consistency["status_field_present"] is False
    assert split_integrity["split_integrity_status"] == "PAYOFF_OBJECTIVE_SPLIT_INTEGRITY_PASSED"
    assert split_integrity["invalid_split_count"] == 0
    assert split_integrity["all_splits_temporally_valid"] is True
    for split in walk_forward["split_rows"]:
        assert pd.Timestamp(split["train_start"]) <= pd.Timestamp(split["train_end"])
        assert pd.Timestamp(split["train_end"]) <= pd.Timestamp(split["test_start"])
        assert pd.Timestamp(split["test_start"]) < pd.Timestamp(split["test_end"])

    result = _validate_in_workspace(v1401_workspace)
    assert result["status"] == "PAYOFF_OBJECTIVE_REPORTS_CONSISTENT_VALID_SPLITS_EXPLORATORY_ONLY"
    assert result["issues"] == []


def test_split_integrity_marks_empty_train_windows_as_skipped() -> None:
    frame = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                ["2024-08-01T00:00:00Z", "2024-08-15T00:00:00Z", "2024-09-01T00:00:00Z"],
                utc=True,
            )
        }
    )
    report = build_walk_forward_split_integrity(frame)
    assert report["split_integrity_status"] in {"PAYOFF_OBJECTIVE_SPLIT_INTEGRITY_PASSED", "PAYOFF_OBJECTIVE_SPLIT_INTEGRITY_FAILED"}
    assert report["skipped_split_count"] >= 1
    assert report["skipped_splits"][0]["skip_reason"] == "NO_PRIOR_TRAINING_HISTORY"


def test_validator_rejects_split_order_mutation(v1401_workspace: Path, tmp_path: Path) -> None:
    _copy_reports_tree(v1401_workspace, tmp_path)
    split_path = tmp_path / "reports/research/payoff_objective_split_integrity_v1_40_1.json"
    split_data = _load_json(split_path)
    split_data["evaluated_splits"][0]["train_start"] = "2024-07-01T00:00:00+00:00"
    split_data["evaluated_splits"][0]["train_end"] = "2024-01-01T00:00:00+00:00"
    split_path.write_text(json.dumps(split_data, indent=2, ensure_ascii=False), encoding="utf-8")

    result = _validate_in_workspace(tmp_path)
    assert result["status"] == "PAYOFF_OBJECTIVE_REPORTS_INCONSISTENT"
    assert any("temporal ordering" in issue for issue in result["issues"])


def test_validator_rejects_short_overfit_status(v1401_workspace: Path, tmp_path: Path) -> None:
    _copy_reports_tree(v1401_workspace, tmp_path)
    summary_path = tmp_path / "reports/research/payoff_objective_research_summary_v1_40_1.json"
    summary = _load_json(summary_path)
    summary["overfit_guard_status"] = "MODERATE"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    result = _validate_in_workspace(tmp_path)
    assert result["status"] == "PAYOFF_OBJECTIVE_REPORTS_INCONSISTENT"
    assert any("overfit_guard_status" in issue for issue in result["issues"])
