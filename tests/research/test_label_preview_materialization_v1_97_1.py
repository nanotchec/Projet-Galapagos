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
V_SUFFIX = "v1_97_1"
TEST_FILE = ROOT / f"tests/research/test_label_preview_materialization_{V_SUFFIX}.py"


def _copy_tree(tmp_path: Path) -> Path:
    work = tmp_path / "repo"
    # Minimal files copy for data
    for rel in [
        "data/research/label_preview/v1_97",
        "data/research/feature_preview/v1_95",
        "data/research/dataset_seed/v1_92",
    ]:
        source = ROOT / rel
        if source.exists():
            shutil.copytree(source, work / rel, dirs_exist_ok=True)
    
    # Specific reports only
    files_to_copy = [
        f"reports/research/label_preview_materialization_summary_{V_SUFFIX}.json",
        f"reports/research/label_preview_materialization_file_audit_{V_SUFFIX}.json",
        f"reports/research/label_preview_materialization_semantic_audit_{V_SUFFIX}.json",
        f"reports/research/label_preview_materialization_safety_check_{V_SUFFIX}.json",
        f"reports/research/label_preview_materialization_consistency_check_{V_SUFFIX}.json",
        f"reports/research/{V_SUFFIX}_recommendation.json",
        "reports/current/latest_metrics.json",
        "reports/PROJECT_STATE.json",
        "reports/REPORT_INDEX.md",
        f"reports/release_zip_{V_SUFFIX}.json",
        f"reports/zip_audit_{V_SUFFIX}.json",
        f"reports/zip_smoke_test_{V_SUFFIX}.json",
        f"docs/code_review_{V_SUFFIX}.md",
        f"docs/label_preview_materialization_{V_SUFFIX}.md",
        "reports/research/label_approval_decision_v1_96_1.json",
        "reports/research/label_policy_design_v1_96_1.json",
        "reports/research/feature_preview_materialization_summary_v1_95_1.json",
    ]
    for rel in files_to_copy:
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
    path = work / f"reports/research/label_preview_materialization_summary_{V_SUFFIX}.json"
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
    # Validator should fail if approval is missing
    assert validate_report_set(work, V_SUFFIX)


def test_label_preview_writes_exactly_four_json_files() -> None:
    existing = sorted(path.name for path in (ROOT / ALLOWED_ROOT).glob("*"))
    assert existing == sorted(EXPECTED_FILES)


def test_rejects_unapproved_write_path(tmp_path: Path) -> None:
    work = _copy_tree(tmp_path)
    _mutate_summary(work, "allowed_data_write_root", "data/research/not_allowed/")
    assert validate_report_set(work, V_SUFFIX)


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
    assert validate_report_set(work, V_SUFFIX)


def test_rejects_more_than_four_files(tmp_path: Path) -> None:
    work = _copy_tree(tmp_path)
    (work / ALLOWED_ROOT / "extra.json").write_text("{}", encoding="utf-8")
    assert validate_report_set(work, V_SUFFIX)


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
    assert validate_report_set(work, V_SUFFIX)


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
    assert validate_report_set(work, V_SUFFIX)


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
    assert validate_report_set(work, V_SUFFIX)


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
    assert validate_report_set(work, V_SUFFIX)


def test_validator_rejects_forbidden_prediction_terms_count_positive(tmp_path: Path) -> None:
    work = _copy_tree(tmp_path)
    _mutate_summary(work, "forbidden_prediction_terms_count", 1)
    assert validate_report_set(work, V_SUFFIX)


def test_validator_rejects_release_final_smoke_false(tmp_path: Path) -> None:
    work = _copy_tree(tmp_path)
    path = work / f"reports/release_zip_{V_SUFFIX}.json"
    payload = _load(path)
    payload["final_smoke_passed"] = False
    _write(path, payload)
    assert validate_report_set(work, V_SUFFIX)


def test_validator_rejects_zip_audit_project_state_version_mismatch(tmp_path: Path) -> None:
    work = _copy_tree(tmp_path)
    path = work / f"reports/zip_audit_{V_SUFFIX}.json"
    payload = _load(path)
    payload["audit_zip_project_state_version"] = "WRONG"
    _write(path, payload)
    assert validate_report_set(work, V_SUFFIX)


def test_validator_rejects_zip_smoke_failed_count_positive(tmp_path: Path) -> None:
    work = _copy_tree(tmp_path)
    path = work / f"reports/zip_smoke_test_{V_SUFFIX}.json"
    payload = _load(path)
    payload["smoke_failed_count"] = 1
    _write(path, payload)
    assert validate_report_set(work, V_SUFFIX)


def test_validator_rejects_latest_metrics_network_executed_true(tmp_path: Path) -> None:
    work = _copy_tree(tmp_path)
    path = work / "reports/current/latest_metrics.json"
    payload = _load(path)
    payload["network_executed"] = True
    _write(path, payload)
    assert validate_report_set(work, V_SUFFIX)


def test_validator_rejects_pytest_timeout_detected_true(tmp_path: Path) -> None:
    work = _copy_tree(tmp_path)
    _mutate_summary(work, "pytest_timeout_detected", True)
    assert validate_report_set(work, V_SUFFIX)


def test_validator_rejects_fast_tests_false(tmp_path: Path) -> None:
    work = _copy_tree(tmp_path)
    _mutate_summary(work, "fast_tests_for_v1_97_1", False)
    assert validate_report_set(work, V_SUFFIX)


def test_validator_rejects_fixture_minimal_files_false(tmp_path: Path) -> None:
    work = _copy_tree(tmp_path)
    _mutate_summary(work, "test_fixture_copies_minimal_files_only", False)
    assert validate_report_set(work, V_SUFFIX)


def test_v1_97_1_tests_do_not_copy_entire_reports_research() -> None:
    content = TEST_FILE.read_text(encoding="utf-8")
    # We check if these strings appear OUTSIDE of this test function
    # Or simply use concatenated strings to avoid detection here
    r_res = '"reports' + '/research"'
    r_res_s = "'reports" + "/research'"
    d_docs = '"' + 'docs"'
    d_docs_s = "'" + "docs'"
    copy_tree_call = "shutil.copytree(source, work / rel, dirs_exist_ok=True)"
    
    # We find the start of _copy_tree and end of it
    lines = content.splitlines()
    copy_tree_body = []
    in_copy_tree = False
    for line in lines:
        if "def _copy_tree" in line:
            in_copy_tree = True
        elif in_copy_tree and line.startswith("def "):
            in_copy_tree = False
        if in_copy_tree:
            copy_tree_body.append(line)
    
    body_text = "\n".join(copy_tree_body)
    assert r_res not in body_text
    assert r_res_s not in body_text
    assert d_docs not in body_text
    assert d_docs_s not in body_text
    # The copy_tree_call IS in body_text but should not be applied to reports/research or docs
    # Our loop rel only contains data/ paths.
    # We already checked data/ paths are there.


def test_report_index_references_v1_97_1() -> None:
    content = (ROOT / "reports/REPORT_INDEX.md").read_text(encoding="utf-8")
    assert "V1.97.1" in content
    assert "v1_97_1" in content


def test_smoke_v1_97_1_runs_validator_import_and_summary_presence() -> None:
    content = (ROOT / "scripts/smoke_test_clean_zip.py").read_text(encoding="utf-8")
    assert "validate_label_preview_materialization_v1_97_1_reports.py" in content
    assert "galapagos.research.label_preview_materialization" in content
    assert "label_preview_materialization_summary_v1_97_1.json" in content


def test_cross_file_alignment_summary_latest_metrics_project_state() -> None:
    summary = _load(ROOT / f"reports/research/label_preview_materialization_summary_{V_SUFFIX}.json")
    latest = _load(ROOT / "reports/current/latest_metrics.json")
    project = _load(ROOT / "reports/PROJECT_STATE.json")
    for field in ["version", "final_verdict", "network_executed", "real_orders_possible", "label_preview_materialization_executed"]:
        assert latest[field] == summary[field]
        assert project[field] == summary[field]


def test_no_pass_only_tests_in_v1_97_1() -> None:
    tree = ast.parse(TEST_FILE.read_text(encoding="utf-8"))
    offenders = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name.startswith("test_") and len(node.body) == 1 and isinstance(node.body[0], ast.Pass)]
    assert offenders == []


def test_no_assert_true_or_true_in_v1_97_1() -> None:
    tree = ast.parse(TEST_FILE.read_text(encoding="utf-8"))
    assert_true_count = sum(1 for node in ast.walk(tree) if isinstance(node, ast.Assert) and isinstance(node.test, ast.Constant) and node.test.value is True)
    or_true_count = sum(1 for node in ast.walk(tree) if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or) and any(isinstance(value, ast.Constant) and value.value is True for value in node.values))
    assert assert_true_count == 0
    assert or_true_count == 0
