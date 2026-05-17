from __future__ import annotations

import ast
import json
import shutil
from pathlib import Path

import pytest

from galapagos.research.label_preview_materialization.feature_preview_reader import FeaturePreviewReader
from galapagos.research.label_preview_materialization.label_preview_builder import ALLOWED_ROOT, EXPECTED_FILES
from galapagos.research.label_preview_materialization.label_semantic_guard import scan_label_payloads
from galapagos.research.label_preview_materialization.physical_auditor import LabelPreviewPhysicalAuditor
from galapagos.research.label_preview_materialization.validator import validate_report_set

ROOT = Path(__file__).resolve().parents[2]
TEST_FILE = ROOT / "tests/research/test_label_preview_materialization_v1_97.py"


def _copy_tree(tmp_path: Path) -> Path:
    work = tmp_path / "repo"
    for rel in [
        "data/research/label_preview/v1_97",
        "data/research/feature_preview/v1_95",
        "data/research/dataset_seed/v1_92",
        "reports/research",
        "reports/current",
        "docs",
    ]:
        source = ROOT / rel
        if source.exists():
            shutil.copytree(source, work / rel, dirs_exist_ok=True)
    for rel in ["reports/PROJECT_STATE.json", "reports/REPORT_INDEX.md", "reports/release_zip_v1_97.json", "reports/zip_audit_v1_97.json", "reports/zip_smoke_test_v1_97.json"]:
        source = ROOT / rel
        if source.exists():
            (work / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, work / rel)
    return work


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _mutate_summary(work: Path, field: str, value: object) -> None:
    path = work / "reports/research/label_preview_materialization_summary_v1_97.json"
    payload = _load(path)
    payload[field] = value
    _write(path, payload)


def test_requires_v1_96_approval() -> None:
    approval = _load(ROOT / "reports/research/label_approval_decision_v1_96_1.json")
    assert approval["human_approval_granted"] is True
    assert approval["v1_97_authorized"] is True


def test_rejects_missing_approval(tmp_path: Path) -> None:
    work = _copy_tree(tmp_path)
    (work / "reports/research/label_approval_decision_v1_96_1.json").unlink()
    assert not (work / "reports/research/label_approval_decision_v1_96_1.json").exists()


def test_label_preview_writes_exactly_four_json_files() -> None:
    existing = sorted(path.name for path in (ROOT / ALLOWED_ROOT).glob("*"))
    assert existing == sorted(EXPECTED_FILES)


def test_rejects_unapproved_write_path(tmp_path: Path) -> None:
    work = _copy_tree(tmp_path)
    _mutate_summary(work, "allowed_data_write_root", "data/research/not_allowed/")
    assert validate_report_set(work, "v1_97")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("created_files_count", 5),
        ("total_data_bytes_written", 50001),
        ("label_preview_rows_count", 11),
        ("theoretical_labels_count", 6),
    ],
)
def test_validator_rejects_limit_violations(tmp_path: Path, field: str, value: object) -> None:
    work = _copy_tree(tmp_path)
    _mutate_summary(work, field, value)
    assert validate_report_set(work, "v1_97")


def test_rejects_more_than_four_files(tmp_path: Path) -> None:
    work = _copy_tree(tmp_path)
    (work / ALLOWED_ROOT / "extra.json").write_text("{}", encoding="utf-8")
    assert validate_report_set(work, "v1_97")


def test_rejects_bytes_over_limit(tmp_path: Path) -> None:
    test_validator_rejects_limit_violations(tmp_path, "total_data_bytes_written", 50001)


def test_rejects_label_preview_rows_above_10(tmp_path: Path) -> None:
    test_validator_rejects_limit_violations(tmp_path, "label_preview_rows_count", 11)


def test_rejects_theoretical_labels_above_5(tmp_path: Path) -> None:
    test_validator_rejects_limit_violations(tmp_path, "theoretical_labels_count", 6)


@pytest.mark.parametrize("name", ["bad.parquet", "bad.csv", "bad.sqlite", "bad.jsonl", "bad.db"])
def test_rejects_forbidden_file_types(tmp_path: Path, name: str) -> None:
    work = _copy_tree(tmp_path)
    (work / ALLOWED_ROOT / name).write_text("x", encoding="utf-8")
    assert validate_report_set(work, "v1_97")


def test_rejects_parquet_created(tmp_path: Path) -> None:
    test_rejects_forbidden_file_types(tmp_path, "bad.parquet")


def test_rejects_csv_created(tmp_path: Path) -> None:
    test_rejects_forbidden_file_types(tmp_path, "bad.csv")


def test_rejects_sqlite_created(tmp_path: Path) -> None:
    test_rejects_forbidden_file_types(tmp_path, "bad.sqlite")


def test_rejects_jsonl_created(tmp_path: Path) -> None:
    test_rejects_forbidden_file_types(tmp_path, "bad.jsonl")


def test_rejects_db_created(tmp_path: Path) -> None:
    test_rejects_forbidden_file_types(tmp_path, "bad.db")


@pytest.mark.parametrize(
    "field",
    [
        "predictions_created",
        "model_training_executed",
        "ml_signal_validation_executed",
        "network_executed",
        "trading_allowed",
        "real_orders_possible",
        "existing_feature_preview_files_modified",
        "existing_seed_files_modified",
        "feature_label_join_created",
        "training_dataset_created",
        "labels_available_at_decision_ts",
    ],
)
def test_rejects_forbidden_true_flags(tmp_path: Path, field: str) -> None:
    work = _copy_tree(tmp_path)
    _mutate_summary(work, field, True)
    assert validate_report_set(work, "v1_97")


def test_rejects_predictions_created(tmp_path: Path) -> None:
    test_rejects_forbidden_true_flags(tmp_path, "predictions_created")


def test_rejects_model_training_executed(tmp_path: Path) -> None:
    test_rejects_forbidden_true_flags(tmp_path, "model_training_executed")


def test_rejects_ml_signal_validation_executed(tmp_path: Path) -> None:
    test_rejects_forbidden_true_flags(tmp_path, "ml_signal_validation_executed")


def test_rejects_network_executed(tmp_path: Path) -> None:
    test_rejects_forbidden_true_flags(tmp_path, "network_executed")


def test_rejects_trading_allowed(tmp_path: Path) -> None:
    test_rejects_forbidden_true_flags(tmp_path, "trading_allowed")


def test_rejects_real_orders_possible(tmp_path: Path) -> None:
    test_rejects_forbidden_true_flags(tmp_path, "real_orders_possible")


def test_rejects_existing_feature_preview_files_modified(tmp_path: Path) -> None:
    test_rejects_forbidden_true_flags(tmp_path, "existing_feature_preview_files_modified")


def test_rejects_existing_seed_files_modified(tmp_path: Path) -> None:
    test_rejects_forbidden_true_flags(tmp_path, "existing_seed_files_modified")


def test_rejects_feature_label_join_created(tmp_path: Path) -> None:
    test_rejects_forbidden_true_flags(tmp_path, "feature_label_join_created")


def test_rejects_training_dataset_created(tmp_path: Path) -> None:
    test_rejects_forbidden_true_flags(tmp_path, "training_dataset_created")


def test_rejects_labels_available_at_decision_ts_true(tmp_path: Path) -> None:
    test_rejects_forbidden_true_flags(tmp_path, "labels_available_at_decision_ts")


def test_rejects_label_available_after_horizon_false(tmp_path: Path) -> None:
    work = _copy_tree(tmp_path)
    _mutate_summary(work, "label_available_after_horizon", False)
    assert validate_report_set(work, "v1_97")


@pytest.mark.parametrize(
    "term",
    ["prediction_score", "model_training", "trade_signal", "real_order_execution", "pnl_profit_ev_mfe_mae"],
)
def test_semantic_guard_rejects_forbidden_terms(term: str) -> None:
    scan = scan_label_payloads({"x.json": {"field": term}})
    assert scan["forbidden_prediction_terms_detected"] is True
    assert scan["forbidden_prediction_terms_count"] >= 1


def test_rejects_prediction_score_anywhere() -> None:
    test_semantic_guard_rejects_forbidden_terms("prediction_score")


def test_rejects_model_training_terms_anywhere() -> None:
    test_semantic_guard_rejects_forbidden_terms("model_training")


def test_rejects_trade_signal_terms_anywhere() -> None:
    test_semantic_guard_rejects_forbidden_terms("trade_signal")


def test_rejects_order_execution_terms_anywhere() -> None:
    test_semantic_guard_rejects_forbidden_terms("real_order_execution")


def test_manifest_contains_checksums() -> None:
    manifest = _load(ROOT / ALLOWED_ROOT / "label_preview_manifest.json")
    assert sorted(manifest["label_preview_file_checksums"]) == sorted([name for name in EXPECTED_FILES if name != "label_preview_manifest.json"])


def test_label_files_json_valid() -> None:
    assert LabelPreviewPhysicalAuditor(ROOT).audit()["label_files_json_valid"] is True


def test_validator_rejects_forbidden_prediction_terms_detected_true(tmp_path: Path) -> None:
    work = _copy_tree(tmp_path)
    _mutate_summary(work, "forbidden_prediction_terms_detected", True)
    assert validate_report_set(work, "v1_97")


def test_validator_rejects_forbidden_prediction_terms_count_positive(tmp_path: Path) -> None:
    work = _copy_tree(tmp_path)
    _mutate_summary(work, "forbidden_prediction_terms_count", 1)
    assert validate_report_set(work, "v1_97")


def test_report_index_references_v1_97() -> None:
    content = (ROOT / "reports/REPORT_INDEX.md").read_text(encoding="utf-8")
    assert "V1.97" in content
    assert "v1_97" in content


def test_smoke_v1_97_runs_validator_import_and_summary_presence() -> None:
    content = (ROOT / "scripts/smoke_test_clean_zip.py").read_text(encoding="utf-8")
    assert "validate_label_preview_materialization_v1_97_reports.py" in content
    assert "galapagos.research.label_preview_materialization" in content
    assert "label_preview_materialization_summary_v1_97.json" in content


def test_cross_file_alignment_summary_latest_metrics_project_state() -> None:
    summary = _load(ROOT / "reports/research/label_preview_materialization_summary_v1_97.json")
    latest = _load(ROOT / "reports/current/latest_metrics.json")
    project = _load(ROOT / "reports/PROJECT_STATE.json")
    for field in ["version", "final_verdict", "network_executed", "real_orders_possible", "label_preview_materialization_executed"]:
        assert latest[field] == summary[field]
        assert project[field] == summary[field]


def test_no_pass_only_tests_in_v1_97() -> None:
    tree = ast.parse(TEST_FILE.read_text(encoding="utf-8"))
    offenders = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name.startswith("test_") and len(node.body) == 1 and isinstance(node.body[0], ast.Pass)]
    assert offenders == []


def test_no_assert_true_or_true_in_v1_97() -> None:
    tree = ast.parse(TEST_FILE.read_text(encoding="utf-8"))
    assert_true_count = sum(1 for node in ast.walk(tree) if isinstance(node, ast.Assert) and isinstance(node.test, ast.Constant) and node.test.value is True)
    or_true_count = sum(1 for node in ast.walk(tree) if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or) and any(isinstance(value, ast.Constant) and value.value is True for value in node.values))
    assert assert_true_count == 0
    assert or_true_count == 0

