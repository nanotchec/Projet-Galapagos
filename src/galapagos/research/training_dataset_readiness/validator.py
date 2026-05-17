from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

from .feature_preview_reviewer import FeaturePreviewReviewer
from .label_preview_reviewer import LabelPreviewReviewer

V_DISP = "V1.98.2"
V_SUFFIX = "v1_98_2"

CRITICAL_FIELDS = [
    "version",
    "final_verdict",
    "post_label_preview_review_executed",
    "feature_preview_review_executed",
    "label_preview_review_executed",
    "feature_label_alignment_dry_run_executed",
    "feature_label_alignment_dry_run_reports_only",
    "training_dataset_policy_created",
    "approval_gate_only",
    "reports_only",
    "physical_feature_label_join_created",
    "training_dataset_created",
    "training_dataset_files_created_in_data",
    "predictions_created",
    "model_training_executed",
    "ml_signal_validation_executed",
    "backtest_executed",
    "data_directory_write_attempted",
    "new_data_files_created",
    "network_executed",
    "trading_allowed",
    "real_orders_possible",
    "v1_99_execution_attempted",
    "feature_preview_checksums_verified",
    "label_preview_checksums_verified",
    "feature_rows_timestamp_order_valid",
    "labels_separated_from_features",
    "labels_available_at_decision_ts",
    "label_available_after_horizon",
    "physical_label_timestamp_audit_executed",
    "label_timestamp_order_valid",
    "label_timestamp_violations_detected",
    "label_timestamp_violations_count",
    "label_timestamp_violations",
    "alignment_dry_run_created",
    "alignment_dry_run_reports_only",
    "alignment_dry_run_data_write_allowed",
    "alignment_preview_rows_count",
    "alignment_pairs_count",
    "labels_joined_to_features_for_training",
    "labels_available_at_feature_decision_ts",
    "alignment_leakage_detected",
    "alignment_lookahead_detected",
    "future_training_dataset_materialization_requires_v1_98_approval",
    "future_training_dataset_max_files",
    "future_training_dataset_max_bytes",
    "future_training_dataset_no_network",
    "future_training_dataset_no_ml",
    "future_training_dataset_no_backtest",
    "future_training_dataset_no_trading",
    "purge_policy_defined",
    "embargo_policy_defined",
    "temporal_split_policy_defined",
    "no_random_shuffle_policy_defined",
    "label_availability_policy_defined",
    "strict_alignment_report_validation",
    "strict_training_dataset_policy_validation",
    "release_ready_for_external_review",
    "clean_zip_ready_for_external_review",
    "smoke_test_passed",
    "blocking_reason",
]


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _required_paths(version_suffix: str) -> dict[str, str]:
    return {
        "summary": f"reports/research/training_dataset_readiness_summary_{version_suffix}.json",
        "feature_review": f"reports/research/training_dataset_feature_preview_review_{version_suffix}.json",
        "label_review": f"reports/research/training_dataset_label_preview_review_{version_suffix}.json",
        "alignment": f"reports/research/training_dataset_alignment_dryrun_{version_suffix}.json",
        "policy": f"reports/research/training_dataset_policy_{version_suffix}.json",
        "approval": f"reports/research/training_dataset_approval_decision_{version_suffix}.json",
        "safety": f"reports/research/training_dataset_readiness_safety_check_{version_suffix}.json",
        "consistency": f"reports/research/training_dataset_readiness_consistency_check_{version_suffix}.json",
        "latest": "reports/current/latest_metrics.json",
        "project": "reports/PROJECT_STATE.json",
        "index": "reports/REPORT_INDEX.md",
        "release": f"reports/release_zip_{version_suffix}.json",
        "audit": f"reports/zip_audit_{version_suffix}.json",
        "smoke": f"reports/zip_smoke_test_{version_suffix}.json",
        "code_review": f"docs/code_review_{version_suffix}.md",
        "doc": f"docs/training_dataset_readiness_{version_suffix}.md",
    }


def _validate_release_audit_smoke(release: dict[str, Any], audit: dict[str, Any], smoke: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field, expected in {
        "version": V_DISP,
        "release_zip_created": True,
        "final_zip_created": True,
        "release_ready_for_external_review": True,
        "clean_zip_ready_for_external_review": True,
        "final_audit_passed": True,
        "final_smoke_passed": True,
        "blocking_reason": None,
    }.items():
        if release.get(field) != expected:
            errors.append(f"release: {field} != {expected}")
    for field, expected in {
        "version": V_DISP,
        "clean_zip_ready_for_external_review": True,
        "audit_zip_project_state_version": V_DISP,
        "audit_zip_version_parse_correct": True,
        "global_json_finiteness_passed": True,
        "missing_required_files": [],
        "forbidden_count": 0,
    }.items():
        if audit.get(field) != expected:
            errors.append(f"audit: {field} != {expected}")
    for field, expected in {
        "version": V_DISP,
        "smoke_test_passed": True,
        "smoke_failed_count": 0,
        "smoke_commands_not_empty": True,
        "bounded_smoke_for_v1_98_2": True,
        "real_orders_possible": False,
        "codex_cli_called": False,
        "holdout_executed": False,
    }.items():
        if smoke.get(field) != expected:
            errors.append(f"smoke: {field} != {expected}")
    if smoke.get("smoke_passed_count") != smoke.get("smoke_commands_count"):
        errors.append("smoke: smoke_passed_count != smoke_commands_count")
    return errors


def _check_test_quality(root: Path) -> list[str]:
    path = root / "tests/research/test_training_dataset_readiness_v1_98_2.py"
    if not path.exists():
        return ["missing V1.98.2 tests"]
    tree = ast.parse(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_") and len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            errors.append(f"pass-only test: {node.name}")
        if isinstance(node, ast.Assert) and isinstance(node.test, ast.Constant) and node.test.value is True:
            errors.append("assert True found")
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
            if any(isinstance(value, ast.Constant) and value.value is True for value in node.values):
                errors.append("or True found")
    return errors


def validate_report_set(root: Path, version_suffix: str = V_SUFFIX) -> list[str]:
    if version_suffix != V_SUFFIX:
        return [f"unsupported version: {version_suffix}"]
    errors: list[str] = []
    loaded: dict[str, dict[str, Any]] = {}
    for key, rel in _required_paths(version_suffix).items():
        path = root / rel
        if not path.exists():
            errors.append(f"missing {rel}")
            continue
        if path.suffix == ".json":
            loaded[key] = _load(path)
            if not path.with_suffix(".md").exists():
                errors.append(f"missing markdown for {rel}")
    if errors:
        return errors

    summary = loaded["summary"]
    expected_values: dict[str, Any] = {
        "version": V_DISP,
        "final_verdict": "V1_98_2_STRICT_ALIGNMENT_AND_POLICY_VALIDATION_PASSED",
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
        "feature_preview_checksums_verified": True,
        "label_preview_checksums_verified": True,
        "feature_rows_timestamp_order_valid": True,
        "labels_separated_from_features": True,
        "labels_available_at_decision_ts": False,
        "label_available_after_horizon": True,
        "physical_label_timestamp_audit_executed": True,
        "label_timestamp_order_valid": True,
        "label_timestamp_violations_detected": False,
        "label_timestamp_violations_count": 0,
        "label_timestamp_violations": [],
        "alignment_dry_run_created": True,
        "alignment_dry_run_reports_only": True,
        "alignment_dry_run_data_write_allowed": False,
        "labels_joined_to_features_for_training": False,
        "labels_available_at_feature_decision_ts": False,
        "alignment_leakage_detected": False,
        "alignment_lookahead_detected": False,
        "future_training_dataset_materialization_requires_v1_98_approval": True,
        "future_training_dataset_no_network": True,
        "future_training_dataset_no_ml": True,
        "future_training_dataset_no_backtest": True,
        "future_training_dataset_no_trading": True,
        "purge_policy_defined": True,
        "embargo_policy_defined": True,
        "temporal_split_policy_defined": True,
        "no_random_shuffle_policy_defined": True,
        "label_availability_policy_defined": True,
        "strict_alignment_report_validation": True,
        "strict_training_dataset_policy_validation": True,
        "release_ready_for_external_review": True,
        "clean_zip_ready_for_external_review": True,
        "smoke_test_passed": True,
        "blocking_reason": None,
    }
    for field, expected in expected_values.items():
        if summary.get(field) != expected:
            errors.append(f"summary: {field} != {expected} (got {summary.get(field)})")
    if summary.get("alignment_preview_rows_count", 0) > 10:
        errors.append("summary: alignment_preview_rows_count > 10")
    if summary.get("alignment_pairs_count", 0) > 10:
        errors.append("summary: alignment_pairs_count > 10")
    if summary.get("future_training_dataset_max_files", 0) > 5:
        errors.append("summary: future_training_dataset_max_files > 5")
    if summary.get("future_training_dataset_max_bytes", 0) > 75000:
        errors.append("summary: future_training_dataset_max_bytes > 75000")
    if summary.get("approval_phrase_match") is False and summary.get("human_approval_granted") is True:
        errors.append("summary: human approval granted despite phrase mismatch")
    if summary.get("human_approval_granted") is True:
        if summary.get("authorized_future_version") != "V1.99":
            errors.append("summary: authorized_future_version != V1.99")
        if summary.get("authorized_future_scope") != "training_dataset_preview_materialization_ultra_bounded_no_network_no_ml_no_backtest_no_trading":
            errors.append("summary: authorized_future_scope mismatch")

    for field in CRITICAL_FIELDS:
        if field not in summary:
            errors.append(f"summary missing {field}")
            continue
        for label, payload in [("latest", loaded["latest"]), ("project", loaded["project"])]:
            if field not in payload:
                errors.append(f"{label} missing {field}")
            elif payload[field] != summary[field]:
                errors.append(f"{label}: {field} diverges from summary")

    errors.extend(_validate_release_audit_smoke(loaded["release"], loaded["audit"], loaded["smoke"]))
    errors.extend(_validate_alignment_report(loaded["alignment"]))
    errors.extend(_validate_training_dataset_policy(loaded["policy"]))
    feature_audit = FeaturePreviewReviewer(root).audit()
    label_audit = LabelPreviewReviewer(root).audit()
    for field in [
        "reviewed_feature_preview_files_count",
        "unexpected_feature_preview_files_count",
        "missing_feature_preview_files_count",
        "feature_preview_checksums_verified",
        "feature_preview_json_valid",
        "feature_rows_timestamp_order_valid",
        "forbidden_feature_terms_detected",
        "forbidden_feature_terms_count",
        "target_like_fields_detected",
        "future_information_fields_detected",
        "prediction_like_fields_detected",
    ]:
        if summary.get(field) != feature_audit.get(field):
            errors.append(f"feature physical audit mismatch: {field}")
    for field in [
        "reviewed_label_preview_files_count",
        "unexpected_label_preview_files_count",
        "missing_label_preview_files_count",
        "label_preview_checksums_verified",
        "label_preview_json_valid",
        "labels_available_at_decision_ts",
        "label_available_after_horizon",
        "physical_label_timestamp_audit_executed",
        "label_timestamp_order_valid",
        "label_timestamp_violations_detected",
        "label_timestamp_violations_count",
        "label_timestamp_violations",
        "forbidden_prediction_terms_detected",
        "forbidden_prediction_terms_count",
        "prediction_like_fields_detected",
        "model_training_terms_detected",
        "trading_signal_terms_detected",
        "order_execution_terms_detected",
    ]:
        if summary.get(field) != label_audit.get(field):
            errors.append(f"label physical audit mismatch: {field}")

    if f"v1_98_2" not in (root / "reports/REPORT_INDEX.md").read_text(encoding="utf-8"):
        errors.append("REPORT_INDEX missing v1_98_2")
    errors.extend(_check_test_quality(root))
    return errors


def _validate_alignment_report(alignment: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected = {
        "version": V_DISP,
        "alignment_dry_run_created": True,
        "alignment_dry_run_reports_only": True,
        "alignment_dry_run_data_write_allowed": False,
        "feature_label_join_preview_in_reports_only": True,
        "physical_feature_label_join_created": False,
        "training_dataset_created": False,
        "training_dataset_files_created_in_data": False,
        "labels_joined_to_features_for_training": False,
        "labels_available_at_feature_decision_ts": False,
        "alignment_leakage_detected": False,
        "alignment_lookahead_detected": False,
    }
    for field, expected_value in expected.items():
        if alignment.get(field) != expected_value:
            errors.append(f"alignment: {field} != {expected_value}")
    if alignment.get("alignment_preview_rows_count", 0) > 10:
        errors.append("alignment: alignment_preview_rows_count > 10")
    if alignment.get("alignment_pairs_count", 0) > 10:
        errors.append("alignment: alignment_pairs_count > 10")
    rows = alignment.get("alignment_preview_rows", [])
    if not isinstance(rows, list):
        errors.append("alignment: alignment_preview_rows must be a list")
    else:
        if len(rows) > 10:
            errors.append("alignment: alignment_preview_rows length > 10")
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                errors.append(f"alignment: row {index} is not an object")
                continue
            if row.get("reports_only") is not True:
                errors.append(f"alignment: row {index} reports_only != true")
            if row.get("physical_join_created") is not False:
                errors.append(f"alignment: row {index} physical_join_created != false")
            if row.get("usable_for_training_in_v1_98_1") is True or row.get("usable_for_training_in_v1_98_2") is True:
                errors.append(f"alignment: row {index} usable_for_training true")
    return errors


def _validate_training_dataset_policy(policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected = {
        "version": V_DISP,
        "training_dataset_policy_created": True,
        "future_training_dataset_materialization_requires_v1_98_approval": True,
        "future_training_dataset_allowed_root": "data/research/training_dataset_preview/v1_99/",
        "future_training_dataset_allowed_extensions": [".json"],
        "future_training_dataset_no_network": True,
        "future_training_dataset_no_ml": True,
        "future_training_dataset_no_backtest": True,
        "future_training_dataset_no_trading": True,
        "purge_policy_defined": True,
        "embargo_policy_defined": True,
        "temporal_split_policy_defined": True,
        "no_random_shuffle_policy_defined": True,
        "label_availability_policy_defined": True,
    }
    for field, expected_value in expected.items():
        if policy.get(field) != expected_value:
            errors.append(f"policy: {field} != {expected_value}")
    if policy.get("future_training_dataset_max_files", 0) > 5:
        errors.append("policy: future_training_dataset_max_files > 5")
    if policy.get("future_training_dataset_max_bytes", 0) > 75000:
        errors.append("policy: future_training_dataset_max_bytes > 75000")
    return errors
