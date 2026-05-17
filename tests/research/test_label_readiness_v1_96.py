from __future__ import annotations

import ast
import json
import shutil
from pathlib import Path

import pytest

from galapagos.research.label_readiness.approval_gate import APPROVAL_PHRASE, AUTHORIZED_SCOPE, LabelApprovalGate
from galapagos.research.label_readiness.feature_preview_reviewer import EXPECTED_FEATURE_FILES, FEATURE_PREVIEW_ROOT, FeaturePreviewReviewer
from galapagos.research.label_readiness.label_dryrun import LabelDryRun
from galapagos.research.label_readiness.label_policy_designer import LabelPolicyDesigner
from galapagos.research.label_readiness.validator import validate_report_set

ROOT = Path(__file__).resolve().parents[2]
TEST_FILE = ROOT / "tests/research/test_label_readiness_v1_96.py"


def _copy_tree(tmp_path: Path) -> Path:
    work = tmp_path / "repo"
    for rel in [
        "data/research/feature_preview/v1_95",
        "data/research/dataset_seed/v1_92",
        "reports/research",
        "reports/current",
        "docs",
    ]:
        source = ROOT / rel
        if source.exists():
            shutil.copytree(source, work / rel, dirs_exist_ok=True)
    for rel in ["reports/PROJECT_STATE.json", "reports/REPORT_INDEX.md", "reports/release_zip_v1_96.json", "reports/zip_audit_v1_96.json", "reports/zip_smoke_test_v1_96.json"]:
        source = ROOT / rel
        if source.exists():
            (work / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, work / rel)
    if (ROOT / "reports/PROJECT_STATE.md").exists():
        (work / "reports").mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / "reports/PROJECT_STATE.md", work / "reports/PROJECT_STATE.md")
    return work


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _mutate_json(path: Path, field: str, value: object) -> None:
    payload = _load(path)
    payload[field] = value
    _write(path, payload)


def test_exact_approval_phrase_grants_future_v1_97_only() -> None:
    decision = LabelApprovalGate().evaluate(APPROVAL_PHRASE)
    assert decision["human_approval_granted"] is True
    assert decision["v1_97_authorized"] is True
    assert decision["authorized_future_version"] == "V1.97"
    assert decision["authorized_future_scope"] == AUTHORIZED_SCOPE


def test_wrong_approval_phrase_denies() -> None:
    decision = LabelApprovalGate().evaluate(APPROVAL_PHRASE + " ")
    assert decision["human_approval_granted"] is False
    assert decision["v1_97_authorized"] is False
    assert decision["authorized_future_version"] is None


def test_approval_does_not_execute_v1_97() -> None:
    assert LabelApprovalGate().evaluate(APPROVAL_PHRASE)["v1_97_execution_attempted"] is False


def test_approval_does_not_write_data() -> None:
    decision = LabelApprovalGate().evaluate(APPROVAL_PHRASE)
    assert "data_directory_write_attempted" not in decision


def test_feature_preview_review_reads_only(tmp_path: Path) -> None:
    work = _copy_tree(tmp_path)
    before = {name: (work / FEATURE_PREVIEW_ROOT / name).read_bytes() for name in EXPECTED_FEATURE_FILES}
    audit = FeaturePreviewReviewer(work).audit()
    after = {name: (work / FEATURE_PREVIEW_ROOT / name).read_bytes() for name in EXPECTED_FEATURE_FILES}
    assert audit["feature_preview_review_physical_audit_executed"] is True
    assert after == before


def test_feature_preview_review_rejects_missing_feature_file(tmp_path: Path) -> None:
    work = _copy_tree(tmp_path)
    (work / FEATURE_PREVIEW_ROOT / "feature_preview_schema.json").unlink()
    assert FeaturePreviewReviewer(work).audit()["missing_feature_preview_files_count"] == 1


def test_feature_preview_review_rejects_extra_feature_file(tmp_path: Path) -> None:
    work = _copy_tree(tmp_path)
    (work / FEATURE_PREVIEW_ROOT / "extra.json").write_text("{}", encoding="utf-8")
    assert FeaturePreviewReviewer(work).audit()["unexpected_feature_preview_files_count"] == 1


def test_feature_preview_review_rejects_checksum_mismatch(tmp_path: Path) -> None:
    work = _copy_tree(tmp_path)
    path = work / FEATURE_PREVIEW_ROOT / "feature_preview_schema.json"
    payload = _load(path)
    payload["checksum_breaker"] = "changed"
    _write(path, payload)
    assert FeaturePreviewReviewer(work).audit()["feature_preview_checksums_verified"] is False


def test_feature_preview_review_rejects_available_ts_after_decision_ts(tmp_path: Path) -> None:
    work = _copy_tree(tmp_path)
    path = work / FEATURE_PREVIEW_ROOT / "feature_preview_rows.json"
    payload = _load(path)
    payload["rows"][0]["available_ts"] = "2026-01-01T00:00:03Z"
    _write(path, payload)
    assert FeaturePreviewReviewer(work).audit()["feature_rows_timestamp_order_valid"] is False


def test_feature_preview_review_rejects_event_ts_after_available_ts(tmp_path: Path) -> None:
    work = _copy_tree(tmp_path)
    path = work / FEATURE_PREVIEW_ROOT / "feature_preview_rows.json"
    payload = _load(path)
    payload["rows"][0]["event_ts"] = "2026-01-01T00:00:02Z"
    _write(path, payload)
    assert FeaturePreviewReviewer(work).audit()["timestamp_order_violations_count"] == 1


def test_label_policy_created() -> None:
    assert LabelPolicyDesigner().design()["label_policy_created"] is True


def test_label_dryrun_preview_created_in_reports_only() -> None:
    dryrun = LabelDryRun().build({"feature_preview_rows.json": {"rows": [{"event_ts": "a", "available_ts": "b", "decision_ts": "c"}]}})
    assert dryrun["label_dry_run_preview_created"] is True
    assert dryrun["label_dry_run_preview_in_reports_only"] is True


def test_label_dryrun_does_not_write_data() -> None:
    assert LabelDryRun().build({"feature_preview_rows.json": {"rows": []}})["label_dry_run_data_write_allowed"] is False


def test_label_dryrun_preview_rows_limited_to_10() -> None:
    rows = [{"event_ts": "a", "available_ts": "b", "decision_ts": "c"} for _ in range(20)]
    dryrun = LabelDryRun().build({"feature_preview_rows.json": {"rows": rows}})
    assert dryrun["label_dry_run_preview_rows_count"] <= 10


def test_label_dryrun_theoretical_labels_limited_to_5() -> None:
    assert LabelDryRun().build({"feature_preview_rows.json": {"rows": []}})["label_dry_run_theoretical_labels_count"] <= 5


def test_label_policy_requires_label_horizon() -> None:
    assert LabelPolicyDesigner().design()["label_horizon_policy_defined"] is True


def test_label_policy_requires_label_available_after_horizon() -> None:
    assert LabelPolicyDesigner().design()["label_available_after_horizon_policy_defined"] is True


def test_label_policy_forbids_training_labels_in_v1_96() -> None:
    assert LabelPolicyDesigner().design()["labels_for_training_forbidden_in_v1_96"] is True


def test_label_policy_forbids_joining_labels_to_features_in_v1_96() -> None:
    assert LabelPolicyDesigner().design()["labels_joined_to_features_forbidden_in_v1_96"] is True


@pytest.mark.parametrize(
    "field",
    [
        "physical_labels_created",
        "physical_targets_created",
        "labels_created_in_data",
        "targets_created_in_data",
        "predictions_created",
        "model_training_executed",
        "ml_signal_validation_executed",
        "data_directory_write_attempted",
        "network_executed",
        "trading_allowed",
        "real_orders_possible",
        "v1_97_execution_attempted",
    ],
)
def test_validator_rejects_forbidden_true_fields(tmp_path: Path, field: str) -> None:
    work = _copy_tree(tmp_path)
    _mutate_json(work / "reports/research/label_readiness_summary_v1_96.json", field, True)
    assert validate_report_set(work, "v1_96")


def test_validator_rejects_physical_labels_created_true(tmp_path: Path) -> None:
    test_validator_rejects_forbidden_true_fields(tmp_path, "physical_labels_created")


def test_validator_rejects_physical_targets_created_true(tmp_path: Path) -> None:
    test_validator_rejects_forbidden_true_fields(tmp_path, "physical_targets_created")


def test_validator_rejects_labels_created_in_data_true(tmp_path: Path) -> None:
    test_validator_rejects_forbidden_true_fields(tmp_path, "labels_created_in_data")


def test_validator_rejects_targets_created_in_data_true(tmp_path: Path) -> None:
    test_validator_rejects_forbidden_true_fields(tmp_path, "targets_created_in_data")


def test_validator_rejects_predictions_created_true(tmp_path: Path) -> None:
    test_validator_rejects_forbidden_true_fields(tmp_path, "predictions_created")


def test_validator_rejects_model_training_executed_true(tmp_path: Path) -> None:
    test_validator_rejects_forbidden_true_fields(tmp_path, "model_training_executed")


def test_validator_rejects_ml_signal_validation_executed_true(tmp_path: Path) -> None:
    test_validator_rejects_forbidden_true_fields(tmp_path, "ml_signal_validation_executed")


def test_validator_rejects_data_write_attempted_true(tmp_path: Path) -> None:
    test_validator_rejects_forbidden_true_fields(tmp_path, "data_directory_write_attempted")


def test_validator_rejects_network_executed_true(tmp_path: Path) -> None:
    test_validator_rejects_forbidden_true_fields(tmp_path, "network_executed")


def test_validator_rejects_trading_allowed_true(tmp_path: Path) -> None:
    test_validator_rejects_forbidden_true_fields(tmp_path, "trading_allowed")


def test_validator_rejects_real_orders_possible_true(tmp_path: Path) -> None:
    test_validator_rejects_forbidden_true_fields(tmp_path, "real_orders_possible")


def test_validator_rejects_v1_97_execution_attempted_true(tmp_path: Path) -> None:
    test_validator_rejects_forbidden_true_fields(tmp_path, "v1_97_execution_attempted")


def test_validator_rejects_label_dryrun_data_write_allowed_true(tmp_path: Path) -> None:
    work = _copy_tree(tmp_path)
    _mutate_json(work / "reports/research/label_dryrun_preview_v1_96.json", "label_dry_run_data_write_allowed", True)
    assert validate_report_set(work, "v1_96")


def test_validator_rejects_label_horizon_policy_missing(tmp_path: Path) -> None:
    work = _copy_tree(tmp_path)
    _mutate_json(work / "reports/research/label_readiness_summary_v1_96.json", "label_horizon_policy_defined", False)
    assert validate_report_set(work, "v1_96")


def test_validator_rejects_labels_joined_to_features_allowed(tmp_path: Path) -> None:
    work = _copy_tree(tmp_path)
    _mutate_json(work / "reports/research/label_readiness_summary_v1_96.json", "labels_joined_to_features_forbidden_in_v1_96", False)
    assert validate_report_set(work, "v1_96")


def test_validator_rejects_release_final_smoke_false(tmp_path: Path) -> None:
    work = _copy_tree(tmp_path)
    _mutate_json(work / "reports/release_zip_v1_96.json", "final_smoke_passed", False)
    assert validate_report_set(work, "v1_96")


def test_validator_rejects_zip_audit_project_state_version_mismatch(tmp_path: Path) -> None:
    work = _copy_tree(tmp_path)
    _mutate_json(work / "reports/zip_audit_v1_96.json", "audit_zip_project_state_version", "V1.95.1")
    assert validate_report_set(work, "v1_96")


def test_validator_rejects_zip_smoke_failed_count_positive(tmp_path: Path) -> None:
    work = _copy_tree(tmp_path)
    _mutate_json(work / "reports/zip_smoke_test_v1_96.json", "smoke_failed_count", 1)
    assert validate_report_set(work, "v1_96")


def test_report_index_references_v1_96() -> None:
    content = (ROOT / "reports/REPORT_INDEX.md").read_text(encoding="utf-8")
    assert "V1.96" in content
    assert "v1_96" in content


def test_smoke_v1_96_runs_validator_import_and_summary_presence() -> None:
    content = (ROOT / "scripts/smoke_test_clean_zip.py").read_text(encoding="utf-8")
    assert "validate_label_readiness_v1_96_reports.py" in content
    assert "galapagos.research.label_readiness" in content
    assert "label_readiness_summary_v1_96.json" in content


def test_cross_file_alignment_summary_latest_metrics_project_state() -> None:
    summary = _load(ROOT / "reports/research/label_readiness_summary_v1_96.json")
    latest = _load(ROOT / "reports/current/latest_metrics.json")
    project = _load(ROOT / "reports/PROJECT_STATE.json")
    for field in ["version", "final_verdict", "network_executed", "dataset_created", "real_orders_possible"]:
        assert latest[field] == summary[field]
        assert project[field] == summary[field]


def test_no_pass_only_tests_in_v1_96() -> None:
    tree = ast.parse(TEST_FILE.read_text(encoding="utf-8"))
    offenders = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_") and len(node.body) == 1 and isinstance(node.body[0], ast.Pass)
    ]
    assert offenders == []


def test_no_assert_true_or_true_in_v1_96() -> None:
    tree = ast.parse(TEST_FILE.read_text(encoding="utf-8"))
    assert_true_count = sum(1 for node in ast.walk(tree) if isinstance(node, ast.Assert) and isinstance(node.test, ast.Constant) and node.test.value is True)
    or_true_count = sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.BoolOp)
        and isinstance(node.op, ast.Or)
        and any(isinstance(value, ast.Constant) and value.value is True for value in node.values)
    )
    assert assert_true_count == 0
    assert or_true_count == 0

