from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

from .feature_reader import FeaturePreviewReader
from .label_reader import LabelPreviewReader
from .physical_auditor import TrainingDatasetPreviewPhysicalAuditor

V_DISP = "V1.99"
V_SUFFIX = "v1_99"

CRITICAL_FIELDS = [
    "version",
    "final_verdict",
    "training_dataset_preview_materialization_executed",
    "training_dataset_preview_only",
    "physical_training_dataset_preview_created",
    "training_dataset_files_created_in_data",
    "full_training_dataset_created",
    "predictions_created",
    "model_training_executed",
    "ml_signal_validation_executed",
    "backtest_executed",
    "trading_allowed",
    "real_orders_possible",
    "total_new_data_files_created",
    "created_files_count",
    "total_data_bytes_written",
    "training_preview_rows_count",
    "joined_feature_label_pairs_count",
    "feature_preview_checksums_verified",
    "label_preview_checksums_verified",
    "feature_rows_timestamp_order_valid",
    "label_timestamp_order_valid",
    "labels_available_at_decision_ts",
    "label_available_after_horizon",
    "labels_joined_to_features_for_training",
    "training_preview_for_research_only",
    "anti_leakage_join_guard_applied",
    "label_availability_policy_applied",
    "purge_policy_applied",
    "embargo_policy_applied",
    "temporal_split_policy_applied",
    "no_random_shuffle_policy_applied",
    "alignment_leakage_detected",
    "alignment_lookahead_detected",
    "training_dataset_leakage_detected",
    "training_dataset_lookahead_detected",
    "split_policy_created",
    "purge_policy_defined",
    "embargo_policy_defined",
    "temporal_split_policy_defined",
    "no_random_shuffle_policy_defined",
    "random_shuffle_used",
    "prediction_like_fields_detected",
    "model_training_terms_detected",
    "backtest_terms_detected",
    "trading_signal_terms_detected",
    "order_execution_terms_detected",
    "network_executed",
    "v1_99_authorized",
    "unapproved_data_write_detected",
    "existing_feature_preview_files_modified",
    "existing_label_preview_files_modified",
    "existing_seed_files_modified",
    "release_ready_for_external_review",
    "clean_zip_ready_for_external_review",
    "smoke_test_passed",
    "blocking_reason",
]


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _required_paths(version_suffix: str) -> dict[str, str]:
    return {
        "summary": f"reports/research/training_dataset_preview_materialization_summary_{version_suffix}.json",
        "file_audit": f"reports/research/training_dataset_preview_materialization_file_audit_{version_suffix}.json",
        "semantic_audit": f"reports/research/training_dataset_preview_materialization_semantic_audit_{version_suffix}.json",
        "leakage_audit": f"reports/research/training_dataset_preview_materialization_leakage_audit_{version_suffix}.json",
        "safety": f"reports/research/training_dataset_preview_materialization_safety_check_{version_suffix}.json",
        "consistency": f"reports/research/training_dataset_preview_materialization_consistency_check_{version_suffix}.json",
        "latest": "reports/current/latest_metrics.json",
        "project": "reports/PROJECT_STATE.json",
        "index": "reports/REPORT_INDEX.md",
        "release": f"reports/release_zip_{version_suffix}.json",
        "audit": f"reports/zip_audit_{version_suffix}.json",
        "smoke": f"reports/zip_smoke_test_{version_suffix}.json",
        "code_review": f"docs/code_review_{version_suffix}.md",
        "doc": f"docs/training_dataset_preview_materialization_{version_suffix}.md",
    }


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
    expected = {
        "version": V_DISP,
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
        "feature_preview_checksums_verified": True,
        "label_preview_checksums_verified": True,
        "feature_rows_timestamp_order_valid": True,
        "label_timestamp_order_valid": True,
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
        "network_executed": False,
        "v1_99_authorized": True,
        "unapproved_data_write_detected": False,
        "existing_feature_preview_files_modified": False,
        "existing_label_preview_files_modified": False,
        "existing_seed_files_modified": False,
        "release_ready_for_external_review": True,
        "clean_zip_ready_for_external_review": True,
        "smoke_test_passed": True,
        "blocking_reason": None,
    }
    for field, expected_value in expected.items():
        if summary.get(field) != expected_value:
            errors.append(f"summary: {field} != {expected_value}")
    for field, expected_value in {
        "total_new_data_files_created": 5,
        "created_files_count": 5,
    }.items():
        if summary.get(field) != expected_value:
            errors.append(f"summary: {field} != {expected_value}")
    for field, limit in {
        "total_data_bytes_written": 75000,
        "training_preview_rows_count": 10,
        "joined_feature_label_pairs_count": 10,
    }.items():
        if summary.get(field, 0) > limit:
            errors.append(f"summary: {field} > {limit}")
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
    physical = TrainingDatasetPreviewPhysicalAuditor(root).audit()
    for field in [
        "training_dataset_preview_json_valid",
        "training_dataset_preview_checksums_verified",
        "forbidden_files_detected",
        "total_data_bytes_written",
        "training_preview_rows_count",
        "joined_feature_label_pairs_count",
        "split_policy_created",
        "purge_policy_defined",
        "embargo_policy_defined",
        "temporal_split_policy_defined",
        "no_random_shuffle_policy_defined",
        "random_shuffle_used",
        "training_dataset_leakage_detected",
        "training_dataset_lookahead_detected",
        "prediction_like_fields_detected",
        "model_training_terms_detected",
        "backtest_terms_detected",
        "trading_signal_terms_detected",
        "order_execution_terms_detected",
    ]:
        expected_value = False if field == "forbidden_files_detected" else physical.get(field)
        if summary.get(field) != expected_value:
            errors.append(f"physical V1.99 mismatch: {field}")
    if physical.get("missing_training_dataset_preview_files_count") != 0:
        errors.append("physical V1.99 missing expected files")
    if physical.get("unexpected_training_dataset_preview_files_count") != 0:
        errors.append("physical V1.99 unexpected files")
    if physical.get("training_dataset_preview_checksums_verified") is not True:
        errors.append("physical V1.99 checksum mismatch")
    if physical.get("forbidden_training_preview_terms_detected") is True:
        errors.append("physical V1.99 forbidden semantic terms detected")
    feature_audit = FeaturePreviewReader(root).audit()
    label_audit = LabelPreviewReader(root).audit()
    for field in ["feature_preview_checksums_verified", "feature_rows_timestamp_order_valid"]:
        if summary.get(field) != feature_audit.get(field):
            errors.append(f"feature source mismatch: {field}")
    for field in ["label_preview_checksums_verified", "label_timestamp_order_valid", "label_timestamp_violations_detected", "label_timestamp_violations_count", "labels_available_at_decision_ts", "label_available_after_horizon"]:
        if summary.get(field) != label_audit.get(field):
            errors.append(f"label source mismatch: {field}")
    if "v1_99" not in (root / "reports/REPORT_INDEX.md").read_text(encoding="utf-8"):
        errors.append("REPORT_INDEX missing v1_99")
    errors.extend(_check_test_quality(root))
    return errors


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
        "bounded_smoke_for_v1_99": True,
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
    path = root / "tests/research/test_training_dataset_preview_materialization_v1_99.py"
    if not path.exists():
        return ["missing V1.99 tests"]
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
