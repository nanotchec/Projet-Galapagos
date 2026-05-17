from __future__ import annotations

import ast
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from galapagos.research.training_dataset_preview_materialization.join_builder import TrainingDatasetPreviewBuilder
from galapagos.research.training_dataset_preview_materialization.validator import validate_report_set

TEST_FILE = ROOT / "tests/research/test_training_dataset_preview_materialization_v1_99.py"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_md(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Report\n", encoding="utf-8")


def _copy_sources(work: Path) -> None:
    for rel in [
        "data/research/feature_preview/v1_95",
        "data/research/label_preview/v1_97",
        "data/research/dataset_seed/v1_92",
    ]:
        shutil.copytree(ROOT / rel, work / rel)


def _summary() -> dict:
    return {
        "version": "V1.99",
        "version_suffix": "v1_99",
        "final_verdict": "V1_99_TRAINING_DATASET_PREVIEW_MATERIALIZATION_ULTRA_BOUNDED_PASSED",
        "training_dataset_preview_materialization_executed": True,
        "training_dataset_preview_only": True,
        "physical_training_dataset_preview_created": True,
        "training_dataset_files_created_in_data": True,
        "full_training_dataset_created": False,
        "predictions_created": False,
        "model_training_executed": False,
        "ml_signal_validation_executed": False,
        "backtest_executed": False,
        "trading_allowed": False,
        "real_orders_possible": False,
        "network_executed": False,
        "approval_source_verified": True,
        "human_approval_granted": True,
        "approval_phrase_match": True,
        "v1_99_authorized": True,
        "authorized_future_scope": "training_dataset_preview_materialization_ultra_bounded_no_network_no_ml_no_backtest_no_trading",
        "data_directory_writes_allowed": True,
        "data_write_approved": True,
        "data_directory_write_attempted": True,
        "new_data_files_created": True,
        "allowed_data_write_root": "data/research/training_dataset_preview/v1_99/",
        "unapproved_data_write_detected": False,
        "total_new_data_files_created": 5,
        "created_files_count": 5,
        "total_data_bytes_written": 1,
        "training_preview_rows_count": 3,
        "joined_feature_label_pairs_count": 3,
        "training_dataset_preview_json_valid": True,
        "training_dataset_preview_checksums_verified": True,
        "forbidden_files_detected": False,
        "forbidden_training_preview_terms_detected": False,
        "forbidden_training_preview_terms_count": 0,
        "forbidden_training_preview_term_occurrences": [],
        "existing_feature_preview_files_modified": False,
        "existing_label_preview_files_modified": False,
        "existing_seed_files_modified": False,
        "feature_preview_checksums_verified": True,
        "label_preview_checksums_verified": True,
        "feature_rows_timestamp_order_valid": True,
        "label_timestamp_order_valid": True,
        "label_timestamp_violations_detected": False,
        "label_timestamp_violations_count": 0,
        "labels_available_at_decision_ts": False,
        "label_available_after_horizon": True,
        "labels_joined_to_features_for_training": False,
        "training_preview_for_research_only": True,
        "anti_leakage_join_guard_applied": True,
        "label_availability_policy_applied": True,
        "purge_policy_applied": True,
        "embargo_policy_applied": True,
        "temporal_split_policy_applied": True,
        "no_random_shuffle_policy_applied": True,
        "alignment_leakage_detected": False,
        "alignment_lookahead_detected": False,
        "training_dataset_leakage_detected": False,
        "training_dataset_lookahead_detected": False,
        "split_policy_created": True,
        "purge_policy_defined": True,
        "embargo_policy_defined": True,
        "temporal_split_policy_defined": True,
        "no_random_shuffle_policy_defined": True,
        "random_shuffle_used": False,
        "prediction_like_fields_detected": False,
        "model_training_terms_detected": False,
        "backtest_terms_detected": False,
        "trading_signal_terms_detected": False,
        "order_execution_terms_detected": False,
        "release_ready_for_external_review": True,
        "clean_zip_ready_for_external_review": True,
        "smoke_test_passed": True,
        "blocking_reason": None,
    }


def _make_valid_work(tmp_path: Path) -> Path:
    work = tmp_path / "work"
    _copy_sources(work)
    feature_payloads = {path.name: json.loads(path.read_text(encoding="utf-8")) for path in (work / "data/research/feature_preview/v1_95").glob("*.json")}
    label_payloads = {path.name: json.loads(path.read_text(encoding="utf-8")) for path in (work / "data/research/label_preview/v1_97").glob("*.json")}
    builder = TrainingDatasetPreviewBuilder(work)
    stats = builder.write(builder.build_payloads(feature_payloads, label_payloads))
    summary = _summary()
    summary["total_data_bytes_written"] = stats["total_data_bytes_written"]
    reports = [
        "training_dataset_preview_materialization_summary_v1_99",
        "training_dataset_preview_materialization_file_audit_v1_99",
        "training_dataset_preview_materialization_semantic_audit_v1_99",
        "training_dataset_preview_materialization_leakage_audit_v1_99",
        "training_dataset_preview_materialization_safety_check_v1_99",
        "training_dataset_preview_materialization_consistency_check_v1_99",
        "v1_99_recommendation",
    ]
    for name in reports:
        _write_json(work / f"reports/research/{name}.json", summary)
        _write_md(work / f"reports/research/{name}.md")
    for rel in ["reports/PROJECT_STATE.json", "reports/current/latest_metrics.json"]:
        _write_json(work / rel, summary)
    _write_json(work / "reports/release_zip_v1_99.json", {"version": "V1.99", "release_zip_created": True, "final_zip_created": True, "release_ready_for_external_review": True, "clean_zip_ready_for_external_review": True, "final_audit_passed": True, "final_smoke_passed": True, "blocking_reason": None})
    _write_json(work / "reports/zip_audit_v1_99.json", {"version": "V1.99", "clean_zip_ready_for_external_review": True, "audit_zip_project_state_version": "V1.99", "audit_zip_version_parse_correct": True, "global_json_finiteness_passed": True, "missing_required_files": [], "forbidden_count": 0})
    _write_json(work / "reports/zip_smoke_test_v1_99.json", {"version": "V1.99", "smoke_test_passed": True, "smoke_failed_count": 0, "smoke_passed_count": 3, "smoke_commands_count": 3, "smoke_commands_not_empty": True, "bounded_smoke_for_v1_99": True, "real_orders_possible": False, "codex_cli_called": False, "holdout_executed": False})
    for rel in ["reports/release_zip_v1_99.md", "reports/zip_audit_v1_99.md", "reports/zip_smoke_test_v1_99.md", "reports/PROJECT_STATE.md", "reports/current/latest_metrics.md", "reports/current/latest_summary.md", "docs/code_review_v1_99.md", "docs/training_dataset_preview_materialization_v1_99.md"]:
        _write_md(work / rel)
    (work / "reports/REPORT_INDEX.md").parent.mkdir(parents=True, exist_ok=True)
    (work / "reports/REPORT_INDEX.md").write_text("v1_99\n", encoding="utf-8")
    test_target = work / "tests/research/test_training_dataset_preview_materialization_v1_99.py"
    test_target.parent.mkdir(parents=True, exist_ok=True)
    test_target.write_text(TEST_FILE.read_text(encoding="utf-8"), encoding="utf-8")
    return work


def _mutate_summary(work: Path, key: str, value: object) -> None:
    for rel in ["reports/research/training_dataset_preview_materialization_summary_v1_99.json", "reports/PROJECT_STATE.json", "reports/current/latest_metrics.json"]:
        path = work / rel
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload[key] = value
        _write_json(path, payload)


def test_requires_v1_98_approval(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    assert validate_report_set(work, "v1_99") == []


def test_rejects_missing_approval(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    _mutate_summary(work, "v1_99_authorized", False)
    assert validate_report_set(work, "v1_99")


def test_training_dataset_preview_writes_exactly_five_json_files(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    files = sorted(path.name for path in (work / "data/research/training_dataset_preview/v1_99").glob("*.json"))
    assert len(files) == 5


def test_rejects_unapproved_write_path(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    _mutate_summary(work, "unapproved_data_write_detected", True)
    assert validate_report_set(work, "v1_99")


def test_rejects_more_than_five_files(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    _write_json(work / "data/research/training_dataset_preview/v1_99/extra.json", {"extra": "file"})
    assert validate_report_set(work, "v1_99")


def test_rejects_bytes_over_limit(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    _mutate_summary(work, "total_data_bytes_written", 75001)
    assert validate_report_set(work, "v1_99")


def test_rejects_training_preview_rows_above_10(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    _mutate_summary(work, "training_preview_rows_count", 11)
    assert validate_report_set(work, "v1_99")


def test_rejects_joined_feature_label_pairs_above_10(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    _mutate_summary(work, "joined_feature_label_pairs_count", 11)
    assert validate_report_set(work, "v1_99")


def test_rejects_parquet_created(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    (work / "data/research/training_dataset_preview/v1_99/bad.parquet").write_text("bad", encoding="utf-8")
    assert validate_report_set(work, "v1_99")


def test_rejects_csv_created(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    (work / "data/research/training_dataset_preview/v1_99/bad.csv").write_text("bad", encoding="utf-8")
    assert validate_report_set(work, "v1_99")


def test_rejects_sqlite_created(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    (work / "data/research/training_dataset_preview/v1_99/bad.sqlite").write_text("bad", encoding="utf-8")
    assert validate_report_set(work, "v1_99")


def test_rejects_jsonl_created(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    (work / "data/research/training_dataset_preview/v1_99/bad.jsonl").write_text("bad", encoding="utf-8")
    assert validate_report_set(work, "v1_99")


def test_rejects_db_created(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    (work / "data/research/training_dataset_preview/v1_99/bad.db").write_text("bad", encoding="utf-8")
    assert validate_report_set(work, "v1_99")


def test_rejects_existing_feature_preview_files_modified(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    _mutate_summary(work, "existing_feature_preview_files_modified", True)
    assert validate_report_set(work, "v1_99")


def test_rejects_existing_label_preview_files_modified(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    _mutate_summary(work, "existing_label_preview_files_modified", True)
    assert validate_report_set(work, "v1_99")


def test_rejects_existing_seed_files_modified(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    _mutate_summary(work, "existing_seed_files_modified", True)
    assert validate_report_set(work, "v1_99")


def test_rejects_feature_checksum_mismatch(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    _mutate_summary(work, "feature_preview_checksums_verified", False)
    assert validate_report_set(work, "v1_99")


def test_rejects_label_checksum_mismatch(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    _mutate_summary(work, "label_preview_checksums_verified", False)
    assert validate_report_set(work, "v1_99")


def test_rejects_label_available_at_decision_ts_true(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    _mutate_summary(work, "labels_available_at_decision_ts", True)
    assert validate_report_set(work, "v1_99")


def test_rejects_label_available_before_horizon(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    _mutate_summary(work, "label_available_after_horizon", False)
    assert validate_report_set(work, "v1_99")


def test_rejects_training_dataset_leakage_detected_true(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    _mutate_summary(work, "training_dataset_leakage_detected", True)
    assert validate_report_set(work, "v1_99")


def test_rejects_training_dataset_lookahead_detected_true(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    _mutate_summary(work, "training_dataset_lookahead_detected", True)
    assert validate_report_set(work, "v1_99")


def test_rejects_predictions_created_true(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    _mutate_summary(work, "predictions_created", True)
    assert validate_report_set(work, "v1_99")


def test_rejects_prediction_like_fields_detected_true(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    _mutate_summary(work, "prediction_like_fields_detected", True)
    assert validate_report_set(work, "v1_99")


def test_rejects_model_training_executed_true(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    _mutate_summary(work, "model_training_executed", True)
    assert validate_report_set(work, "v1_99")


def test_rejects_ml_signal_validation_executed_true(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    _mutate_summary(work, "ml_signal_validation_executed", True)
    assert validate_report_set(work, "v1_99")


def test_rejects_backtest_executed_true(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    _mutate_summary(work, "backtest_executed", True)
    assert validate_report_set(work, "v1_99")


def test_rejects_backtest_terms_detected_true(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    _mutate_summary(work, "backtest_terms_detected", True)
    assert validate_report_set(work, "v1_99")


def test_rejects_network_executed_true(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    _mutate_summary(work, "network_executed", True)
    assert validate_report_set(work, "v1_99")


def test_rejects_trading_allowed_true(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    _mutate_summary(work, "trading_allowed", True)
    assert validate_report_set(work, "v1_99")


def test_rejects_real_orders_possible_true(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    _mutate_summary(work, "real_orders_possible", True)
    assert validate_report_set(work, "v1_99")


def test_rejects_random_shuffle_used_true(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    _mutate_summary(work, "random_shuffle_used", True)
    assert validate_report_set(work, "v1_99")


def test_rejects_missing_purge_policy(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    _mutate_summary(work, "purge_policy_defined", False)
    assert validate_report_set(work, "v1_99")


def test_rejects_missing_embargo_policy(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    _mutate_summary(work, "embargo_policy_defined", False)
    assert validate_report_set(work, "v1_99")


def test_rejects_missing_temporal_split_policy(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    _mutate_summary(work, "temporal_split_policy_defined", False)
    assert validate_report_set(work, "v1_99")


def test_rejects_release_final_smoke_false(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    path = work / "reports/release_zip_v1_99.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["final_smoke_passed"] = False
    _write_json(path, payload)
    assert validate_report_set(work, "v1_99")


def test_rejects_zip_audit_project_state_version_mismatch(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    path = work / "reports/zip_audit_v1_99.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["audit_zip_project_state_version"] = "V1.98.2"
    _write_json(path, payload)
    assert validate_report_set(work, "v1_99")


def test_rejects_zip_smoke_failed_count_positive(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    path = work / "reports/zip_smoke_test_v1_99.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["smoke_failed_count"] = 1
    _write_json(path, payload)
    assert validate_report_set(work, "v1_99")


def test_report_index_references_v1_99(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    assert "v1_99" in (work / "reports/REPORT_INDEX.md").read_text(encoding="utf-8")


def test_smoke_v1_99_runs_validator_import_and_summary_presence() -> None:
    text = (ROOT / "scripts/smoke_test_clean_zip.py").read_text(encoding="utf-8")
    assert "validate_training_dataset_preview_materialization_v1_99_reports.py" in text
    assert "training_dataset_preview_materialization_summary_v1_99.json" in text


def test_cross_file_alignment_summary_latest_metrics_project_state(tmp_path: Path) -> None:
    work = _make_valid_work(tmp_path)
    assert validate_report_set(work, "v1_99") == []


def test_no_pass_only_tests_in_v1_99() -> None:
    tree = ast.parse(TEST_FILE.read_text(encoding="utf-8"))
    offenders = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name.startswith("test_") and len(node.body) == 1 and isinstance(node.body[0], ast.Pass)]
    assert offenders == []


def test_no_assert_true_or_true_in_v1_99() -> None:
    tree = ast.parse(TEST_FILE.read_text(encoding="utf-8"))
    assert_true = [node.lineno for node in ast.walk(tree) if isinstance(node, ast.Assert) and isinstance(node.test, ast.Constant) and node.test.value is True]
    or_true = [node.lineno for node in ast.walk(tree) if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or) and any(isinstance(value, ast.Constant) and value.value is True for value in node.values)]
    assert assert_true == []
    assert or_true == []
