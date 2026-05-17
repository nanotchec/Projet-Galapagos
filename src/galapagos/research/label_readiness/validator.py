from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

from .feature_preview_reviewer import EXPECTED_FEATURE_FILES, FEATURE_PREVIEW_ROOT, FeaturePreviewReviewer

V_DISP = "V1.96.1"
V_SUFFIX = "v1_96_1"

CRITICAL_FIELDS = [
    "version",
    "final_verdict",
    "post_feature_preview_review_executed",
    "feature_preview_review_only",
    "label_policy_design_executed",
    "label_dry_run_executed",
    "label_dry_run_reports_only",
    "label_dry_run_preview_created",
    "label_dry_run_preview_in_reports_only",
    "approval_gate_only",
    "reports_only",
    "physical_labels_created",
    "physical_targets_created",
    "labels_created_in_data",
    "targets_created_in_data",
    "predictions_created",
    "model_training_executed",
    "ml_signal_validation_executed",
    "data_directory_write_attempted",
    "new_data_files_created",
    "network_executed",
    "trading_allowed",
    "real_orders_possible",
    "v1_97_execution_attempted",
    "feature_preview_checksums_verified",
    "feature_rows_timestamp_order_valid",
    "timestamp_order_violations_detected",
    "label_policy_created",
    "label_dry_run_data_write_allowed",
    "label_dry_run_max_preview_rows",
    "label_dry_run_max_theoretical_labels",
    "label_horizon_policy_defined",
    "label_available_after_horizon_policy_defined",
    "label_not_available_at_decision_ts_policy_defined",
    "labels_for_training_forbidden_in_v1_96",
    "labels_joined_to_features_forbidden_in_v1_96",
    "predictions_forbidden",
    "model_training_forbidden",
    "release_ready_for_external_review",
    "clean_zip_ready_for_external_review",
    "smoke_test_passed",
    "blocking_reason",
]


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _required_paths(version_suffix: str) -> dict[str, str]:
    return {
        "summary": f"reports/research/label_readiness_summary_{version_suffix}.json",
        "feature_review": f"reports/research/label_feature_preview_review_{version_suffix}.json",
        "policy": f"reports/research/label_policy_design_{version_suffix}.json",
        "dryrun": f"reports/research/label_dryrun_preview_{version_suffix}.json",
        "anti_leakage": f"reports/research/label_anti_leakage_audit_{version_suffix}.json",
        "approval": f"reports/research/label_approval_decision_{version_suffix}.json",
        "safety": f"reports/research/label_readiness_safety_check_{version_suffix}.json",
        "consistency": f"reports/research/label_readiness_consistency_check_{version_suffix}.json",
        "latest": "reports/current/latest_metrics.json",
        "project": "reports/PROJECT_STATE.json",
        "index": "reports/REPORT_INDEX.md",
        "release": f"reports/release_zip_{version_suffix}.json",
        "audit": f"reports/zip_audit_{version_suffix}.json",
        "smoke": f"reports/zip_smoke_test_{version_suffix}.json",
        "code_review": f"docs/code_review_{version_suffix}.md",
        "doc": f"docs/label_readiness_{version_suffix}.md",
    }


def _validate_release_audit_smoke(release: dict[str, Any], audit: dict[str, Any], smoke: dict[str, Any], version_suffix: str) -> list[str]:
    errors: list[str] = []
    v_disp_local = "V1.96" if version_suffix == "v1_96" else "V1.96.1"
    bounded_key = "bounded_smoke_for_v1_96" if version_suffix == "v1_96" else "bounded_smoke_for_v1_96_1"
    
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
        "smoke_timeout_detected": False,
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


def _check_test_quality(root: Path, version_suffix: str) -> list[str]:
    path = root / f"tests/research/test_label_readiness_{version_suffix}.py"
    errors: list[str] = []
    if not path.exists():
        return [f"missing {version_suffix.upper()} tests"]
    tree = ast.parse(path.read_text(encoding="utf-8"))
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
    if version_suffix not in ("v1_96", "v1_96_1"):
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
    latest = loaded["latest"]
    project = loaded["project"]
    policy = loaded["policy"]
    
    # Base Expected values for V1.96 and V1.96.1
    v_disp_local = "V1.96" if version_suffix == "v1_96" else "V1.96.1"
    
    expected_values = {
        "version": v_disp_local,
        "post_feature_preview_review_executed": True,
        "feature_preview_review_only": True,
        "label_policy_design_executed": True,
        "label_dry_run_executed": True,
        "label_dry_run_reports_only": True,
        "label_dry_run_preview_created": True,
        "label_dry_run_preview_in_reports_only": True,
        "approval_gate_only": True,
        "reports_only": True,
        "physical_labels_created": False,
        "physical_targets_created": False,
        "labels_created_in_data": False,
        "targets_created_in_data": False,
        "predictions_created": False,
        "model_training_executed": False,
        "ml_signal_validation_executed": False,
        "data_directory_write_attempted": False,
        "new_data_files_created": False,
        "network_executed": False,
        "trading_allowed": False,
        "real_orders_possible": False,
        "v1_97_execution_attempted": False,
        "feature_preview_checksums_verified": True,
        "feature_rows_timestamp_order_valid": True,
        "timestamp_order_violations_detected": False,
        "label_policy_created": True,
        "label_dry_run_data_write_allowed": False,
        "label_horizon_policy_defined": True,
        "label_available_after_horizon_policy_defined": True,
        "label_not_available_at_decision_ts_policy_defined": True,
        "labels_for_training_forbidden_in_v1_96": True,
        "labels_joined_to_features_forbidden_in_v1_96": True,
        "predictions_forbidden": True,
        "model_training_forbidden": True,
        "release_ready_for_external_review": True,
        "clean_zip_ready_for_external_review": True,
        "smoke_test_passed": True,
        "blocking_reason": None,
    }
    
    local_critical_fields = list(CRITICAL_FIELDS)
    
    if version_suffix == "v1_96_1":
        # Add V1.96.1 specific fields to expected values and critical fields
        expected_values["pytest_timeout_detected"] = False
        expected_values["fast_tests_for_v1_96_1"] = True
        expected_values["test_fixture_copies_minimal_files_only"] = True
        expected_values["strict_label_policy_design_validation"] = True
        
        for k in ["pytest_timeout_detected", "fast_tests_for_v1_96_1", "test_fixture_copies_minimal_files_only", "strict_label_policy_design_validation"]:
            if k not in local_critical_fields:
                local_critical_fields.append(k)
                
        # Validate pytest results for timeout
        if summary.get("pytest_timeout_detected") is not False:
            errors.append("summary: pytest_timeout_detected != false")
        if summary.get("pytest_exit_code", 0) != 0:
            errors.append("summary: pytest_exit_code != 0")
        if summary.get("pytest_failed_count", 0) != 0:
            errors.append("summary: pytest_failed_count != 0")
            
        # Strict label policy design validation
        if policy.get("label_policy_created") is not True:
            errors.append("policy: label_policy_created != true")
        if policy.get("label_horizon_policy_defined") is not True:
            errors.append("policy: label_horizon_policy_defined != true")
        if policy.get("label_available_after_horizon_policy_defined") is not True:
            errors.append("policy: label_available_after_horizon_policy_defined != true")
        if policy.get("label_not_available_at_decision_ts_policy_defined") is not True:
            errors.append("policy: label_not_available_at_decision_ts_policy_defined != true")
        if policy.get("labels_for_training_forbidden_in_v1_96") is not True:
            errors.append("policy: labels_for_training_forbidden_in_v1_96 != true")
        if policy.get("labels_joined_to_features_forbidden_in_v1_96") is not True:
            errors.append("policy: labels_joined_to_features_forbidden_in_v1_96 != true")
        if policy.get("predictions_forbidden") is not True:
            errors.append("policy: predictions_forbidden != true")
        if policy.get("model_training_forbidden") is not True:
            errors.append("policy: model_training_forbidden != true")
        if policy.get("trading_forbidden") is not True:
            errors.append("policy: trading_forbidden != true")
        if policy.get("future_label_materialization_requires_v1_96_approval") is not True:
            errors.append("policy: future_label_materialization_requires_v1_96_approval != true")
        if policy.get("future_label_materialization_allowed_root") != "data/research/label_preview/v1_97/":
            errors.append("policy: future_label_materialization_allowed_root != data/research/label_preview/v1_97/")
        if (policy.get("future_label_materialization_max_files") or 0) > 4:
            errors.append("policy: future_label_materialization_max_files > 4")
        if (policy.get("future_label_materialization_max_bytes") or 0) > 50000:
            errors.append("policy: future_label_materialization_max_bytes > 50000")
        if policy.get("future_label_materialization_allowed_extensions") != [".json"]:
            errors.append("policy: future_label_materialization_allowed_extensions != ['.json']")
        if policy.get("future_label_materialization_no_network") is not True:
            errors.append("policy: future_label_materialization_no_network != true")
        if policy.get("future_label_materialization_no_ml") is not True:
            errors.append("policy: future_label_materialization_no_ml != true")
        if policy.get("future_label_materialization_no_trading") is not True:
            errors.append("policy: future_label_materialization_no_trading != true")

    for field, expected in expected_values.items():
        if summary.get(field) != expected:
            errors.append(f"summary: {field} != {expected}")
            
    if (summary.get("label_dry_run_max_preview_rows") or 0) > 10:
        errors.append("label_dry_run_max_preview_rows > 10")
    if (summary.get("label_dry_run_max_theoretical_labels") or 0) > 5:
        errors.append("label_dry_run_max_theoretical_labels > 5")

    for field in local_critical_fields:
        if field not in summary:
            errors.append(f"summary missing critical field {field}")
            continue
        for label, payload in [("latest", latest), ("project", project)]:
            if field not in payload:
                errors.append(f"{label} missing critical field {field}")
            elif payload[field] != summary[field]:
                errors.append(f"{label}: {field} diverges from summary")

    errors.extend(_validate_release_audit_smoke(loaded["release"], loaded["audit"], loaded["smoke"], version_suffix))

    physical = FeaturePreviewReviewer(root).audit()
    for field in [
        "reviewed_feature_preview_files_count",
        "expected_feature_preview_files_count",
        "unexpected_feature_preview_files_count",
        "missing_feature_preview_files_count",
        "feature_preview_checksums_verified",
        "feature_preview_json_valid",
        "preview_rows_count",
        "theoretical_features_count",
        "feature_rows_timestamp_order_valid",
        "timestamp_order_violations_detected",
        "timestamp_order_violations_count",
        "forbidden_feature_terms_detected",
        "forbidden_feature_terms_count",
        "label_like_fields_detected",
        "target_like_fields_detected",
        "prediction_like_fields_detected",
        "future_information_fields_detected",
    ]:
        if summary.get(field) != physical.get(field):
            errors.append(f"summary: {field} diverges from physical review")
    if physical["missing_feature_preview_files_count"] != 0 or physical["unexpected_feature_preview_files_count"] != 0:
        errors.append("feature preview file set mismatch")
    if physical["feature_preview_checksums_verified"] is not True:
        errors.append("feature preview checksums invalid")
    if physical["feature_rows_timestamp_order_valid"] is not True:
        errors.append("feature preview timestamp order invalid")
    if physical["forbidden_feature_terms_detected"]:
        errors.append(f"feature forbidden terms detected: {physical['forbidden_feature_term_occurrences']}")
    existing = sorted(path.name for path in (root / FEATURE_PREVIEW_ROOT).glob("*") if path.is_file())
    if existing != sorted(EXPECTED_FEATURE_FILES):
        errors.append("feature preview files are not exact")

    if loaded["dryrun"].get("label_dry_run_data_write_allowed") is not False:
        errors.append("dryrun data write allowed")
    if loaded["dryrun"].get("label_dry_run_preview_rows_count", 0) > 10:
        errors.append("dryrun preview rows > 10")
    if loaded["dryrun"].get("label_dry_run_theoretical_labels_count", 0) > 5:
        errors.append("dryrun theoretical labels > 5")

    index = (root / "reports/REPORT_INDEX.md").read_text(encoding="utf-8")
    if v_disp_local not in index or version_suffix not in index:
        errors.append(f"REPORT_INDEX does not reference {v_disp_local}")
    errors.extend(_check_test_quality(root, version_suffix))
    return errors
