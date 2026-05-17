from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

from galapagos.research.causal_feature_readiness.seed_reader import SeedReadinessReader

from .feature_preview_builder import ALLOWED_ROOT, EXPECTED_FILES
from .physical_auditor import FeaturePreviewPhysicalAuditor

V_DISP = "V1.95.1"
V_SUFFIX = "v1_95_1"

CRITICAL_FIELDS = [
    "version",
    "final_verdict",
    "feature_preview_materialization_executed",
    "feature_preview_only",
    "physical_features_created",
    "feature_files_created_in_data",
    "full_feature_dataset_created",
    "labels_created",
    "targets_created",
    "predictions_created",
    "model_training_executed",
    "ml_signal_validation_executed",
    "network_executed",
    "trading_allowed",
    "real_orders_possible",
    "total_new_data_files_created",
    "created_files_count",
    "total_data_bytes_written",
    "preview_rows_count",
    "theoretical_features_count",
    "forbidden_feature_terms_detected",
    "forbidden_feature_terms_count",
    "target_like_fields_detected",
    "future_information_fields_detected",
    "label_like_fields_detected",
    "prediction_like_fields_detected",
    "existing_seed_files_modified",
    "release_ready_for_external_review",
    "clean_zip_ready_for_external_review",
    "smoke_test_passed",
    "blocking_reason",
    "physical_timestamp_order_scan_executed",
    "feature_rows_timestamp_order_valid",
    "available_ts_lte_decision_ts_checked",
    "event_ts_lte_available_ts_checked",
    "timestamp_order_violations_detected",
    "timestamp_order_violations_count",
    "timestamp_order_violations",
]


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _required(version_suffix: str) -> dict[str, str]:
    req = {
        "summary": f"reports/research/feature_preview_materialization_summary_{version_suffix}.json",
        "file_audit": f"reports/research/feature_preview_materialization_file_audit_{version_suffix}.json",
        "semantic_audit": f"reports/research/feature_preview_materialization_semantic_audit_{version_suffix}.json",
        "safety": f"reports/research/feature_preview_materialization_safety_check_{version_suffix}.json",
        "consistency": f"reports/research/feature_preview_materialization_consistency_check_{version_suffix}.json",
        "latest": "reports/current/latest_metrics.json",
        "project": "reports/PROJECT_STATE.json",
        "index": "reports/REPORT_INDEX.md",
        "release": f"reports/release_zip_{version_suffix}.json",
        "audit": f"reports/zip_audit_{version_suffix}.json",
        "smoke": f"reports/zip_smoke_test_{version_suffix}.json",
        "code_review": f"docs/code_review_{version_suffix}.md",
        "doc": f"docs/feature_preview_materialization_{version_suffix}.md",
    }
    if version_suffix == "v1_95_1":
        req["timestamp_audit"] = f"reports/research/feature_preview_materialization_timestamp_audit_{version_suffix}.json"
    return req


def _validate_release(release: dict[str, Any], audit: dict[str, Any], smoke: dict[str, Any], version_suffix: str) -> list[str]:
    errors: list[str] = []
    v_disp_local = "V1.95" if version_suffix == "v1_95" else "V1.95.1"
    bounded_key = f"bounded_smoke_for_{version_suffix}"
    for field, expected in {
        "version": v_disp_local,
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
        "version": v_disp_local,
        "clean_zip_ready_for_external_review": True,
        "audit_zip_project_state_version": v_disp_local,
        "audit_zip_version_parse_correct": True,
        "global_json_finiteness_passed": True,
        "missing_required_files": [],
        "forbidden_count": 0,
    }.items():
        if audit.get(field) != expected:
            errors.append(f"audit: {field} != {expected}")
    for field, expected in {
        "version": v_disp_local,
        "smoke_test_passed": True,
        "smoke_failed_count": 0,
        "smoke_commands_not_empty": True,
        bounded_key: True,
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
    path = root / "tests/research/test_feature_preview_materialization_v1_95_1.py"
    if not path.exists():
        return []
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
    if version_suffix not in {"v1_95", "v1_95_1"}:
        return [f"unsupported version: {version_suffix}"]
    errors: list[str] = []
    loaded: dict[str, dict[str, Any]] = {}
    for key, rel in _required(version_suffix).items():
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
    checks = {
        "version": "V1.95" if version_suffix == "v1_95" else "V1.95.1",
        "feature_preview_materialization_executed": True,
        "feature_preview_only": True,
        "physical_features_created": True,
        "feature_files_created_in_data": True,
        "full_feature_dataset_created": False,
        "labels_created": False,
        "targets_created": False,
        "predictions_created": False,
        "model_training_executed": False,
        "ml_signal_validation_executed": False,
        "network_executed": False,
        "trading_allowed": False,
        "real_orders_possible": False,
        "total_new_data_files_created": 4,
        "created_files_count": 4,
        "forbidden_feature_terms_detected": False,
        "forbidden_feature_terms_count": 0,
        "forbidden_feature_term_occurrences": [],
        "target_like_fields_detected": False,
        "future_information_fields_detected": False,
        "label_like_fields_detected": False,
        "prediction_like_fields_detected": False,
        "existing_seed_files_modified": False,
        "release_ready_for_external_review": True,
        "clean_zip_ready_for_external_review": True,
        "smoke_test_passed": True,
        "blocking_reason": None,
    }
    if version_suffix == "v1_95_1":
        checks.update({
            "physical_timestamp_order_scan_executed": True,
            "feature_rows_timestamp_order_valid": True,
            "available_ts_lte_decision_ts_checked": True,
            "event_ts_lte_available_ts_checked": True,
            "timestamp_order_violations_detected": False,
            "timestamp_order_violations_count": 0,
            "timestamp_order_violations": [],
        })
    for field, expected in checks.items():
        if summary.get(field) != expected:
            errors.append(f"summary: {field} != {expected}")
    if summary.get("total_data_bytes_written", 0) > 50000:
        errors.append("summary: total_data_bytes_written > 50000")
    if summary.get("preview_rows_count", 0) > 10:
        errors.append("summary: preview_rows_count > 10")
    if summary.get("theoretical_features_count", 0) > 20:
        errors.append("summary: theoretical_features_count > 20")

    for field in (CRITICAL_FIELDS if version_suffix == "v1_95_1" else [f for f in CRITICAL_FIELDS if f not in {
        "physical_timestamp_order_scan_executed",
        "feature_rows_timestamp_order_valid",
        "available_ts_lte_decision_ts_checked",
        "event_ts_lte_available_ts_checked",
        "timestamp_order_violations_detected",
        "timestamp_order_violations_count",
        "timestamp_order_violations",
    }]):
        if field not in summary:
            errors.append(f"summary missing {field}")
            continue
        for label, payload in [("latest", loaded["latest"]), ("project", loaded["project"])]:
            if field not in payload:
                errors.append(f"{label} missing {field}")
            elif payload[field] != summary[field]:
                errors.append(f"{label}: {field} diverges from summary")

    errors.extend(_validate_release(loaded["release"], loaded["audit"], loaded["smoke"], version_suffix))

    seed = SeedReadinessReader(root).audit()
    if seed["existing_seed_files_modified"] is not False or seed["seed_checksums_verified"] is not True:
        errors.append("seed health check failed")

    physical = FeaturePreviewPhysicalAuditor(root).audit()
    physical_fields = [
        "created_files_count",
        "total_new_data_files_created",
        "total_data_bytes_written",
        "preview_rows_count",
        "theoretical_features_count",
        "forbidden_feature_terms_detected",
        "forbidden_feature_terms_count",
        "forbidden_feature_term_occurrences",
        "target_like_fields_detected",
        "future_information_fields_detected",
        "label_like_fields_detected",
        "prediction_like_fields_detected",
    ]
    if version_suffix == "v1_95_1":
        physical_fields.extend([
            "physical_timestamp_order_scan_executed",
            "feature_rows_timestamp_order_valid",
            "available_ts_lte_decision_ts_checked",
            "event_ts_lte_available_ts_checked",
            "timestamp_order_violations_detected",
            "timestamp_order_violations_count",
            "timestamp_order_violations",
        ])
    for field in physical_fields:
        if summary.get(field) != physical.get(field):
            errors.append(f"summary: {field} diverges from physical audit")
    if physical["missing_expected_files_count"] != 0 or physical["unexpected_files_count"] != 0:
        errors.append("feature preview file set mismatch")
    if physical["feature_preview_json_valid"] is not True:
        errors.append("feature preview JSON invalid")
    if physical["feature_preview_checksums_verified"] is not True:
        errors.append("feature preview checksums invalid")
    if version_suffix == "v1_95_1":
        if physical["feature_rows_timestamp_order_valid"] is not True:
            errors.append("feature rows timestamp order validation failed")
    if physical["total_data_bytes_written"] > 50000:
        errors.append("physical total_data_bytes_written > 50000")
    if physical["preview_rows_count"] > 10:
        errors.append("physical preview_rows_count > 10")
    if physical["theoretical_features_count"] > 20:
        errors.append("physical theoretical_features_count > 20")
    if physical["forbidden_feature_terms_detected"]:
        errors.append(f"forbidden feature terms detected: {physical['forbidden_feature_term_occurrences']}")

    feature_root = root / ALLOWED_ROOT
    existing = sorted(path.name for path in feature_root.glob("*") if path.is_file()) if feature_root.exists() else []
    if existing != sorted(EXPECTED_FILES):
        errors.append("feature preview files are not exact")

    index = (root / "reports/REPORT_INDEX.md").read_text(encoding="utf-8")
    expected_index_term = "V1.95.1" if version_suffix == "v1_95_1" else "V1.95"
    expected_index_suffix = "v1_95_1" if version_suffix == "v1_95_1" else "v1_95"
    if expected_index_term not in index or expected_index_suffix not in index:
        errors.append(f"REPORT_INDEX does not reference {expected_index_term}")
    if version_suffix == "v1_95_1":
        errors.extend(_check_test_quality(root))
    return errors
