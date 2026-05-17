from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

from .feature_preview_reader import FeaturePreviewReader
from .label_preview_builder import ALLOWED_ROOT, EXPECTED_FILES
from .physical_auditor import LabelPreviewPhysicalAuditor

V_DISP_V197 = "V1.97"
V_SUFFIX_V197 = "v1_97"

V_DISP_V1971 = "V1.97.1"
V_SUFFIX_V1971 = "v1_97_1"
V_DISP_V1972 = "V1.97.2"
V_SUFFIX_V1972 = "v1_97_2"

CRITICAL_FIELDS = [
    "version",
    "final_verdict",
    "label_preview_materialization_executed",
    "label_preview_only",
    "physical_labels_created",
    "label_files_created_in_data",
    "physical_targets_created",
    "targets_created_in_data",
    "predictions_created",
    "feature_label_join_created",
    "training_dataset_created",
    "model_training_executed",
    "ml_signal_validation_executed",
    "network_executed",
    "trading_allowed",
    "real_orders_possible",
    "total_new_data_files_created",
    "created_files_count",
    "total_data_bytes_written",
    "label_preview_rows_count",
    "theoretical_labels_count",
    "labels_separated_from_features",
    "labels_available_at_decision_ts",
    "label_available_after_horizon",
    "label_not_available_at_decision_ts_policy_applied",
    "labels_for_training_created",
    "label_preview_for_research_only",
    "forbidden_prediction_terms_detected",
    "forbidden_prediction_terms_count",
    "prediction_like_fields_detected",
    "model_training_terms_detected",
    "trading_signal_terms_detected",
    "order_execution_terms_detected",
    "release_ready_for_external_review",
    "clean_zip_ready_for_external_review",
    "smoke_test_passed",
    "blocking_reason",
]

CRITICAL_FIELDS_V1971 = CRITICAL_FIELDS + [
    "pytest_timeout_detected",
    "fast_tests_for_v1_97_1",
    "test_fixture_copies_minimal_files_only",
]

TIMESTAMP_CRITICAL_FIELDS = [
    "physical_label_timestamp_audit_executed",
    "label_timestamp_order_valid",
    "label_timestamp_violations_detected",
    "label_timestamp_violations_count",
    "label_timestamp_violations",
]

CRITICAL_FIELDS_V1972 = CRITICAL_FIELDS + TIMESTAMP_CRITICAL_FIELDS


def _get_expected_values(version: str) -> dict[str, Any]:
    if version == V_SUFFIX_V1972:
        v_disp = V_DISP_V1972
    elif version == V_SUFFIX_V1971:
        v_disp = V_DISP_V1971
    else:
        v_disp = V_DISP_V197
    base = {
        "version": v_disp,
        "approval_source_verified": True,
        "human_approval_granted": True,
        "approval_phrase_match": True,
        "v1_97_authorized": True,
        "label_preview_materialization_executed": True,
        "label_preview_only": True,
        "physical_labels_created": True,
        "label_files_created_in_data": True,
        "physical_targets_created": False,
        "targets_created_in_data": False,
        "predictions_created": False,
        "feature_label_join_created": False,
        "training_dataset_created": False,
        "model_training_executed": False,
        "ml_signal_validation_executed": False,
        "network_executed": False,
        "trading_allowed": False,
        "real_orders_possible": False,
        "total_new_data_files_created": 4,
        "created_files_count": 4,
        "labels_separated_from_features": True,
        "labels_available_at_decision_ts": False,
        "label_available_after_horizon": True,
        "label_not_available_at_decision_ts_policy_applied": True,
        "labels_for_training_created": False,
        "label_preview_for_research_only": True,
        "forbidden_prediction_terms_detected": False,
        "forbidden_prediction_terms_count": 0,
        "forbidden_prediction_term_occurrences": [],
        "prediction_like_fields_detected": False,
        "model_training_terms_detected": False,
        "trading_signal_terms_detected": False,
        "order_execution_terms_detected": False,
        "release_ready_for_external_review": True,
        "clean_zip_ready_for_external_review": True,
        "smoke_test_passed": True,
        "blocking_reason": None,
    }
    if version == V_SUFFIX_V1971:
        base.update({
            "pytest_timeout_detected": False,
            "fast_tests_for_v1_97_1": True,
            "test_fixture_copies_minimal_files_only": True,
        })
    if version == V_SUFFIX_V1972:
        base.update({
            "physical_label_timestamp_audit_executed": True,
            "label_available_after_horizon": True,
            "labels_available_at_decision_ts": False,
            "label_timestamp_order_valid": True,
            "label_timestamp_violations_detected": False,
            "label_timestamp_violations_count": 0,
            "label_timestamp_violations": [],
        })
    return base


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _required_paths(version_suffix: str) -> dict[str, str]:
    required = {
        "summary": f"reports/research/label_preview_materialization_summary_{version_suffix}.json",
        "file_audit": f"reports/research/label_preview_materialization_file_audit_{version_suffix}.json",
        "semantic_audit": f"reports/research/label_preview_materialization_semantic_audit_{version_suffix}.json",
        "safety": f"reports/research/label_preview_materialization_safety_check_{version_suffix}.json",
        "consistency": f"reports/research/label_preview_materialization_consistency_check_{version_suffix}.json",
        "latest": "reports/current/latest_metrics.json",
        "project": "reports/PROJECT_STATE.json",
        "index": "reports/REPORT_INDEX.md",
        "release": f"reports/release_zip_{version_suffix}.json",
        "audit": f"reports/zip_audit_{version_suffix}.json",
        "smoke": f"reports/zip_smoke_test_{version_suffix}.json",
        "code_review": f"docs/code_review_{version_suffix}.md",
        "doc": f"docs/label_preview_materialization_{version_suffix}.md",
    }
    if version_suffix == V_SUFFIX_V1972:
        required["timestamp_audit"] = f"reports/research/label_preview_materialization_timestamp_audit_{version_suffix}.json"
        required["source_approval"] = "reports/research/label_approval_decision_v1_96_1.json"
    return required


def _validate_release(release: dict[str, Any], audit: dict[str, Any], smoke: dict[str, Any], version_suffix: str) -> list[str]:
    if version_suffix == V_SUFFIX_V1972:
        v_disp = V_DISP_V1972
    elif version_suffix == V_SUFFIX_V1971:
        v_disp = V_DISP_V1971
    else:
        v_disp = V_DISP_V197
    errors: list[str] = []
    for field, expected in {
        "version": v_disp,
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
        "version": v_disp,
        "clean_zip_ready_for_external_review": True,
        "audit_zip_project_state_version": v_disp,
        "audit_zip_version_parse_correct": True,
        "global_json_finiteness_passed": True,
        "missing_required_files": [],
        "forbidden_count": 0,
    }.items():
        if audit.get(field) != expected:
            errors.append(f"audit: {field} != {expected}")
    
    smoke_expectations = {
        "version": v_disp,
        "smoke_test_passed": True,
        "smoke_failed_count": 0,
        "smoke_commands_not_empty": True,
        "real_orders_possible": False,
        "codex_cli_called": False,
        "holdout_executed": False,
    }
    if version_suffix == V_SUFFIX_V1971:
        smoke_expectations["bounded_smoke_for_v1_97_1"] = True
    elif version_suffix == V_SUFFIX_V1972:
        smoke_expectations["bounded_smoke_for_v1_97_2"] = True
    else:
        smoke_expectations["bounded_smoke_for_v1_97"] = True
        
    for field, expected in smoke_expectations.items():
        if smoke.get(field) != expected:
            errors.append(f"smoke: {field} != {expected}")
    if smoke.get("smoke_passed_count") != smoke.get("smoke_commands_count"):
        errors.append("smoke: smoke_passed_count != smoke_commands_count")
    return errors


def _check_test_quality(root: Path, version_suffix: str) -> list[str]:
    path = root / f"tests/research/test_label_preview_materialization_{version_suffix}.py"
    if not path.exists():
        return [f"missing {version_suffix} tests"]
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


def validate_report_set(root: Path, version_suffix: str = V_SUFFIX_V197) -> list[str]:
    if version_suffix not in [V_SUFFIX_V197, V_SUFFIX_V1971, V_SUFFIX_V1972]:
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
            if key != "source_approval" and not path.with_suffix(".md").exists():
                errors.append(f"missing markdown for {rel}")
    if errors:
        return errors
    summary = loaded["summary"]
    expected_values = _get_expected_values(version_suffix)
    for field, expected in expected_values.items():
        if summary.get(field) != expected:
            errors.append(f"summary: {field} != {expected} (got {summary.get(field)})")
    if summary.get("total_data_bytes_written", 0) > 50000:
        errors.append("summary: total_data_bytes_written > 50000")
    if summary.get("label_preview_rows_count", 0) > 10:
        errors.append("summary: label_preview_rows_count > 10")
    if summary.get("theoretical_labels_count", 0) > 5:
        errors.append("summary: theoretical_labels_count > 5")
    
    if version_suffix == V_SUFFIX_V1972:
        fields_to_check = CRITICAL_FIELDS_V1972
    elif version_suffix == V_SUFFIX_V1971:
        fields_to_check = CRITICAL_FIELDS_V1971
    else:
        fields_to_check = CRITICAL_FIELDS
    for field in fields_to_check:
        if field not in summary:
            errors.append(f"summary missing {field}")
            continue
        for label, payload in [("latest", loaded["latest"]), ("project", loaded["project"])]:
            if field not in payload:
                errors.append(f"{label} missing {field}")
            elif payload[field] != summary[field]:
                errors.append(f"{label}: {field} diverges from summary")
    errors.extend(_validate_release(loaded["release"], loaded["audit"], loaded["smoke"], version_suffix))
    feature = FeaturePreviewReader(root)
    feature_audit = feature.audit_feature_preview()
    seed_audit = feature.audit_seed()
    if not feature_audit["feature_preview_checksums_verified"] or not feature_audit["feature_rows_timestamp_order_valid"] or not feature_audit["feature_preview_files_exact"]:
        errors.append("feature preview source audit failed")
    if not seed_audit["seed_files_exact"]:
        errors.append("seed source audit failed")
    physical = LabelPreviewPhysicalAuditor(root).audit()
    for field in [
        "created_files_count",
        "total_new_data_files_created",
        "total_data_bytes_written",
        "label_preview_rows_count",
        "theoretical_labels_count",
        "forbidden_prediction_terms_detected",
        "forbidden_prediction_terms_count",
        "forbidden_prediction_term_occurrences",
        "prediction_like_fields_detected",
        "model_training_terms_detected",
        "trading_signal_terms_detected",
        "order_execution_terms_detected",
        "physical_label_timestamp_audit_executed",
        "label_available_after_horizon",
        "labels_available_at_decision_ts",
        "label_timestamp_order_valid",
        "label_timestamp_violations_detected",
        "label_timestamp_violations_count",
        "label_timestamp_violations",
    ]:
        if summary.get(field) != physical.get(field):
            errors.append(f"summary: {field} diverges from physical audit")
    if version_suffix == V_SUFFIX_V1972:
        for field, expected in {
            "physical_label_timestamp_audit_executed": True,
            "label_available_after_horizon": True,
            "labels_available_at_decision_ts": False,
            "label_timestamp_order_valid": True,
            "label_timestamp_violations_detected": False,
            "label_timestamp_violations_count": 0,
            "label_timestamp_violations": [],
        }.items():
            if physical.get(field) != expected:
                errors.append(f"physical timestamp audit: {field} != {expected}")
    if physical["missing_expected_files_count"] != 0 or physical["unexpected_files_count"] != 0:
        errors.append("label preview file set mismatch")
    if physical["label_files_json_valid"] is not True or physical["label_preview_checksums_verified"] is not True:
        errors.append("label preview JSON/checksums invalid")
    if physical["total_data_bytes_written"] > 50000 or physical["label_preview_rows_count"] > 10 or physical["theoretical_labels_count"] > 5:
        errors.append("label preview physical limits exceeded")
    if physical["forbidden_prediction_terms_detected"]:
        errors.append(f"forbidden semantic terms detected: {physical['forbidden_prediction_term_occurrences']}")
    existing = sorted(path.name for path in (root / ALLOWED_ROOT).glob("*") if path.is_file()) if (root / ALLOWED_ROOT).exists() else []
    if existing != sorted(EXPECTED_FILES):
        errors.append("label preview files are not exact")
    index = (root / "reports/REPORT_INDEX.md").read_text(encoding="utf-8")
    if version_suffix == V_SUFFIX_V1972:
        v_disp = V_DISP_V1972
    elif version_suffix == V_SUFFIX_V1971:
        v_disp = V_DISP_V1971
    else:
        v_disp = V_DISP_V197
    if v_disp not in index or version_suffix not in index:
        errors.append(f"REPORT_INDEX does not reference {v_disp}")
    errors.extend(_check_test_quality(root, version_suffix))
    return errors
