from __future__ import annotations

import ast
import json
import shutil
from pathlib import Path

from galapagos.research.training_dataset_readiness.approval_gate import APPROVAL_PHRASE, AUTHORIZED_SCOPE, TrainingDatasetApprovalGate
from galapagos.research.training_dataset_readiness.feature_preview_reviewer import FeaturePreviewReviewer
from galapagos.research.training_dataset_readiness.label_preview_reviewer import LabelPreviewReviewer
from galapagos.research.training_dataset_readiness.training_dataset_policy import TrainingDatasetPolicyDesigner
from galapagos.research.training_dataset_readiness.validator import validate_report_set

ROOT = Path(__file__).resolve().parents[2]
TEST_FILE = ROOT / "tests/research/test_training_dataset_readiness_v1_98_1.py"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    path.with_suffix(".md").write_text(f"# {path.stem}\n", encoding="utf-8")


def _sha(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _copy_source_files(work: Path) -> None:
    for rel in [
        "data/research/feature_preview/v1_95/feature_preview_manifest.json",
        "data/research/feature_preview/v1_95/feature_preview_schema.json",
        "data/research/feature_preview/v1_95/feature_preview_rows.json",
        "data/research/feature_preview/v1_95/feature_preview_quality_audit.json",
        "data/research/label_preview/v1_97/label_preview_manifest.json",
        "data/research/label_preview/v1_97/label_preview_schema.json",
        "data/research/label_preview/v1_97/label_preview_rows.json",
        "data/research/label_preview/v1_97/label_preview_quality_audit.json",
        "data/research/dataset_seed/v1_92/seed_manifest.json",
        "data/research/dataset_seed/v1_92/seed_schema.json",
        "data/research/dataset_seed/v1_92/seed_preview_records.json",
        "data/research/dataset_seed/v1_92/seed_provenance.json",
        "data/research/dataset_seed/v1_92/seed_quality_audit.json",
    ]:
        target = work / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, target)


def _repair_label_timestamps_for_baseline(work: Path) -> None:
    rows_path = work / "data/research/label_preview/v1_97/label_preview_rows.json"
    payload = json.loads(rows_path.read_text(encoding="utf-8"))
    fixed = ["2026-01-01T00:05:01Z", "2026-01-01T01:05:01Z", "2026-01-01T02:05:01Z"]
    for row, ts in zip(payload["rows"], fixed):
        row["label_available_ts"] = ts
    rows_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest_path = work / "data/research/label_preview/v1_97/label_preview_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["label_preview_file_checksums"]["label_preview_rows.json"] = _sha(rows_path)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def _baseline_repo(tmp_path: Path) -> Path:
    work = tmp_path / "repo"
    _copy_source_files(work)
    _repair_label_timestamps_for_baseline(work)
    feature = FeaturePreviewReviewer(work).audit()
    label = LabelPreviewReviewer(work).audit()
    summary = {
        "version": "V1.98.1",
        "version_suffix": "v1_98_1",
        "final_verdict": "V1_98_1_FEATURE_LABEL_ALIGNMENT_READINESS_WITH_CORRECTED_LABELS_PASSED",
        "post_label_preview_review_executed": True,
        "feature_preview_review_executed": True,
        "label_preview_review_executed": True,
        "feature_label_alignment_dry_run_executed": True,
        "feature_label_alignment_dry_run_reports_only": True,
        "training_dataset_policy_created": True,
        "approval_gate_only": True,
        "reports_only": True,
        "physical_feature_label_join_created": False,
        "training_dataset_created": False,
        "training_dataset_files_created_in_data": False,
        "predictions_created": False,
        "model_training_executed": False,
        "ml_signal_validation_executed": False,
        "backtest_executed": False,
        "data_directory_write_attempted": False,
        "new_data_files_created": False,
        "network_executed": False,
        "trading_allowed": False,
        "real_orders_possible": False,
        "v1_99_execution_attempted": False,
        "alignment_dry_run_created": True,
        "alignment_dry_run_reports_only": True,
        "alignment_dry_run_data_write_allowed": False,
        "alignment_preview_rows_count": 3,
        "alignment_pairs_count": 3,
        "labels_joined_to_features_for_training": False,
        "labels_available_at_feature_decision_ts": False,
        "alignment_leakage_detected": False,
        "alignment_lookahead_detected": False,
        "future_training_dataset_materialization_requires_v1_98_approval": True,
        "future_training_dataset_max_files": 5,
        "future_training_dataset_max_bytes": 75000,
        "future_training_dataset_no_network": True,
        "future_training_dataset_no_ml": True,
        "future_training_dataset_no_backtest": True,
        "future_training_dataset_no_trading": True,
        "purge_policy_defined": True,
        "embargo_policy_defined": True,
        "temporal_split_policy_defined": True,
        "no_random_shuffle_policy_defined": True,
        "label_availability_policy_defined": True,
        "release_ready_for_external_review": True,
        "clean_zip_ready_for_external_review": True,
        "smoke_test_passed": True,
        "blocking_reason": None,
        "approval_phrase_match": True,
        "human_approval_granted": True,
        "authorized_future_version": "V1.99",
        "authorized_future_scope": AUTHORIZED_SCOPE,
        **feature,
        **label,
    }
    for rel in [
        "reports/research/training_dataset_readiness_summary_v1_98_1.json",
        "reports/research/training_dataset_feature_preview_review_v1_98_1.json",
        "reports/research/training_dataset_label_preview_review_v1_98_1.json",
        "reports/research/training_dataset_alignment_dryrun_v1_98_1.json",
        "reports/research/training_dataset_policy_v1_98_1.json",
        "reports/research/training_dataset_approval_decision_v1_98_1.json",
        "reports/research/training_dataset_readiness_safety_check_v1_98_1.json",
        "reports/research/training_dataset_readiness_consistency_check_v1_98_1.json",
        "reports/current/latest_metrics.json",
        "reports/PROJECT_STATE.json",
    ]:
        _write_json(work / rel, summary)
    _write_json(work / "reports/release_zip_v1_98_1.json", {"version": "V1.98.1", "release_zip_created": True, "final_zip_created": True, "release_ready_for_external_review": True, "clean_zip_ready_for_external_review": True, "final_audit_passed": True, "final_smoke_passed": True, "blocking_reason": None})
    _write_json(work / "reports/zip_audit_v1_98_1.json", {"version": "V1.98.1", "clean_zip_ready_for_external_review": True, "audit_zip_project_state_version": "V1.98.1", "audit_zip_version_parse_correct": True, "global_json_finiteness_passed": True, "missing_required_files": [], "forbidden_count": 0})
    _write_json(work / "reports/zip_smoke_test_v1_98_1.json", {"version": "V1.98.1", "smoke_test_passed": True, "smoke_failed_count": 0, "smoke_passed_count": 3, "smoke_commands_count": 3, "smoke_commands_not_empty": True, "bounded_smoke_for_v1_98_1": True, "real_orders_possible": False, "codex_cli_called": False, "holdout_executed": False})
    (work / "docs").mkdir(parents=True, exist_ok=True)
    (work / "docs/code_review_v1_98_1.md").write_text("# Code Review V1.98.1\n", encoding="utf-8")
    (work / "docs/training_dataset_readiness_v1_98_1.md").write_text("# Training Dataset Readiness V1.98.1\n", encoding="utf-8")
    test_target = work / "tests/research/test_training_dataset_readiness_v1_98_1.py"
    test_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TEST_FILE, test_target)
    (work / "reports/REPORT_INDEX.md").parent.mkdir(parents=True, exist_ok=True)
    (work / "reports/REPORT_INDEX.md").write_text("v1_98_1\n", encoding="utf-8")
    return work


def test_exact_approval_phrase_grants_future_v1_99_only() -> None:
    result = TrainingDatasetApprovalGate().evaluate(APPROVAL_PHRASE)
    assert result["v1_99_authorized"] is True
    assert result["authorized_future_scope"] == AUTHORIZED_SCOPE


def test_wrong_approval_phrase_denies() -> None:
    result = TrainingDatasetApprovalGate().evaluate("wrong")
    assert result["human_approval_granted"] is False


def test_approval_does_not_execute_v1_99() -> None:
    assert TrainingDatasetApprovalGate().evaluate(APPROVAL_PHRASE)["v1_99_execution_attempted"] is False


def test_approval_does_not_write_data() -> None:
    assert "data/research" not in AUTHORIZED_SCOPE


def test_feature_preview_review_reads_only(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    before = _sha(work / "data/research/feature_preview/v1_95/feature_preview_rows.json")
    FeaturePreviewReviewer(work).audit()
    assert _sha(work / "data/research/feature_preview/v1_95/feature_preview_rows.json") == before


def test_label_preview_review_reads_only(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    before = _sha(work / "data/research/label_preview/v1_97/label_preview_rows.json")
    LabelPreviewReviewer(work).audit()
    assert _sha(work / "data/research/label_preview/v1_97/label_preview_rows.json") == before


def test_rejects_missing_feature_preview_file(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    (work / "data/research/feature_preview/v1_95/feature_preview_rows.json").unlink()
    assert validate_report_set(work, "v1_98_1")


def test_rejects_missing_label_preview_file(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    (work / "data/research/label_preview/v1_97/label_preview_rows.json").unlink()
    assert validate_report_set(work, "v1_98_1")


def test_rejects_extra_feature_preview_file(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    (work / "data/research/feature_preview/v1_95/extra.json").write_text("{}", encoding="utf-8")
    assert validate_report_set(work, "v1_98_1")


def test_rejects_extra_label_preview_file(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    (work / "data/research/label_preview/v1_97/extra.json").write_text("{}", encoding="utf-8")
    assert validate_report_set(work, "v1_98_1")


def test_rejects_feature_preview_checksum_mismatch(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    (work / "data/research/feature_preview/v1_95/feature_preview_schema.json").write_text("{}", encoding="utf-8")
    assert validate_report_set(work, "v1_98_1")


def test_rejects_label_preview_checksum_mismatch(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    (work / "data/research/label_preview/v1_97/label_preview_schema.json").write_text("{}", encoding="utf-8")
    assert validate_report_set(work, "v1_98_1")


def test_rejects_feature_available_ts_after_decision_ts(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    path = work / "data/research/feature_preview/v1_95/feature_preview_rows.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["rows"][0]["available_ts"] = "2026-01-01T00:00:02Z"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    assert validate_report_set(work, "v1_98_1")


def test_rejects_label_available_at_decision_ts_true(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    path = work / "data/research/label_preview/v1_97/label_preview_rows.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["rows"][0]["label_available_ts"] = payload["rows"][0]["source_decision_ts"]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    assert validate_report_set(work, "v1_98_1")


def test_rejects_label_available_before_horizon(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    path = work / "data/research/label_preview/v1_97/label_preview_rows.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["rows"][1]["label_available_ts"] = "2026-01-01T01:04:59Z"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    assert validate_report_set(work, "v1_98_1")


def test_rejects_label_timestamp_order_valid_false(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    _mutate_summary(work, "label_timestamp_order_valid", False)
    assert validate_report_set(work, "v1_98_1")


def test_alignment_dryrun_created_in_reports_only(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    payload = json.loads((work / "reports/research/training_dataset_alignment_dryrun_v1_98_1.json").read_text())
    assert payload["alignment_dry_run_reports_only"] is True


def test_alignment_dryrun_does_not_write_data(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    payload = json.loads((work / "reports/research/training_dataset_alignment_dryrun_v1_98_1.json").read_text())
    assert payload["alignment_dry_run_data_write_allowed"] is False


def test_alignment_pairs_limited_to_10(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    payload = json.loads((work / "reports/research/training_dataset_readiness_summary_v1_98_1.json").read_text())
    assert payload["alignment_pairs_count"] <= 10


def test_alignment_rejects_labels_available_at_feature_decision_ts(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    path = work / "reports/research/training_dataset_readiness_summary_v1_98_1.json"
    payload = json.loads(path.read_text())
    payload["labels_available_at_feature_decision_ts"] = True
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    assert validate_report_set(work, "v1_98_1")


def test_alignment_rejects_physical_feature_label_join_created(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    _mutate_summary(work, "physical_feature_label_join_created", True)
    assert validate_report_set(work, "v1_98_1")


def test_alignment_rejects_training_dataset_created(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    _mutate_summary(work, "training_dataset_created", True)
    assert validate_report_set(work, "v1_98_1")


def test_training_dataset_policy_created() -> None:
    assert TrainingDatasetPolicyDesigner().design()["training_dataset_policy_created"] is True


def test_training_dataset_policy_requires_future_approval() -> None:
    assert TrainingDatasetPolicyDesigner().design()["future_training_dataset_materialization_requires_v1_98_approval"] is True


def test_training_dataset_policy_rejects_max_files_above_5(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    _mutate_summary(work, "future_training_dataset_max_files", 6)
    assert validate_report_set(work, "v1_98_1")


def test_training_dataset_policy_rejects_max_bytes_above_75000(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    _mutate_summary(work, "future_training_dataset_max_bytes", 75001)
    assert validate_report_set(work, "v1_98_1")


def test_training_dataset_policy_requires_purge_policy(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    _mutate_summary(work, "purge_policy_defined", False)
    assert validate_report_set(work, "v1_98_1")


def test_training_dataset_policy_requires_embargo_policy(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    _mutate_summary(work, "embargo_policy_defined", False)
    assert validate_report_set(work, "v1_98_1")


def test_training_dataset_policy_requires_temporal_split_policy(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    _mutate_summary(work, "temporal_split_policy_defined", False)
    assert validate_report_set(work, "v1_98_1")


def test_training_dataset_policy_forbids_random_shuffle(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    _mutate_summary(work, "no_random_shuffle_policy_defined", False)
    assert validate_report_set(work, "v1_98_1")


def _mutate_summary(work: Path, field: str, value: object) -> None:
    path = work / "reports/research/training_dataset_readiness_summary_v1_98_1.json"
    payload = json.loads(path.read_text())
    payload[field] = value
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_validator_rejects_predictions_created_true(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    _mutate_summary(work, "predictions_created", True)
    assert validate_report_set(work, "v1_98_1")


def test_validator_rejects_model_training_executed_true(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    _mutate_summary(work, "model_training_executed", True)
    assert validate_report_set(work, "v1_98_1")


def test_validator_rejects_ml_signal_validation_executed_true(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    _mutate_summary(work, "ml_signal_validation_executed", True)
    assert validate_report_set(work, "v1_98_1")


def test_validator_rejects_backtest_executed_true(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    _mutate_summary(work, "backtest_executed", True)
    assert validate_report_set(work, "v1_98_1")


def test_validator_rejects_network_executed_true(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    _mutate_summary(work, "network_executed", True)
    assert validate_report_set(work, "v1_98_1")


def test_validator_rejects_trading_allowed_true(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    _mutate_summary(work, "trading_allowed", True)
    assert validate_report_set(work, "v1_98_1")


def test_validator_rejects_real_orders_possible_true(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    _mutate_summary(work, "real_orders_possible", True)
    assert validate_report_set(work, "v1_98_1")


def test_validator_rejects_v1_99_execution_attempted_true(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    _mutate_summary(work, "v1_99_execution_attempted", True)
    assert validate_report_set(work, "v1_98_1")


def test_validator_rejects_release_final_smoke_false(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    path = work / "reports/release_zip_v1_98_1.json"
    payload = json.loads(path.read_text())
    payload["final_smoke_passed"] = False
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    assert validate_report_set(work, "v1_98_1")


def test_validator_rejects_zip_audit_project_state_version_mismatch(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    path = work / "reports/zip_audit_v1_98_1.json"
    payload = json.loads(path.read_text())
    payload["audit_zip_project_state_version"] = "V1.97.2"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    assert validate_report_set(work, "v1_98_1")


def test_validator_rejects_zip_smoke_failed_count_positive(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    path = work / "reports/zip_smoke_test_v1_98_1.json"
    payload = json.loads(path.read_text())
    payload["smoke_failed_count"] = 1
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    assert validate_report_set(work, "v1_98_1")


def test_report_index_references_v1_98_1(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    assert "v1_98_1" in (work / "reports/REPORT_INDEX.md").read_text(encoding="utf-8")


def test_smoke_v1_98_1_runs_validator_import_and_summary_presence() -> None:
    smoke = ROOT / "scripts/smoke_test_clean_zip.py"
    text = smoke.read_text(encoding="utf-8")
    assert "validate_training_dataset_readiness_v1_98_1_reports.py" in text
    assert "training_dataset_readiness_summary_v1_98_1.json" in text


def test_cross_file_alignment_summary_latest_metrics_project_state(tmp_path: Path) -> None:
    work = _baseline_repo(tmp_path)
    assert validate_report_set(work, "v1_98_1") == []


def test_no_pass_only_tests_in_v1_98_1() -> None:
    tree = ast.parse(TEST_FILE.read_text(encoding="utf-8"))
    offenders = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name.startswith("test_") and len(node.body) == 1 and isinstance(node.body[0], ast.Pass)]
    assert offenders == []


def test_no_assert_true_or_true_in_v1_98_1() -> None:
    tree = ast.parse(TEST_FILE.read_text(encoding="utf-8"))
    bad_asserts = [node.lineno for node in ast.walk(tree) if isinstance(node, ast.Assert) and isinstance(node.test, ast.Constant) and node.test.value is True]
    bad_or = [node.lineno for node in ast.walk(tree) if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or) and any(isinstance(value, ast.Constant) and value.value is True for value in node.values)]
    assert bad_asserts == []
    assert bad_or == []
