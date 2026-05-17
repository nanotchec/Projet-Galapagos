from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

from .anti_leakage_feature_guard import scan_forbidden_feature_terms
from .seed_reader import EXPECTED_SEED_FILES, SEED_ROOT, SeedReadinessReader

V_DISP = "V1.94"
V_SUFFIX = "v1_94"

SUMMARY_FIELDS = [
    "version",
    "final_verdict",
    "feature_readiness_pack_executed",
    "feature_schema_design_executed",
    "causal_feature_plan_created",
    "feature_dry_run_executed",
    "feature_dry_run_reports_only",
    "feature_dry_run_preview_created",
    "feature_dry_run_preview_in_reports_only",
    "approval_gate_only",
    "reports_only",
    "feature_generation_executed",
    "physical_features_created",
    "feature_files_created_in_data",
    "labels_created",
    "targets_created",
    "predictions_created",
    "model_training_executed",
    "ml_signal_validation_executed",
    "data_directory_write_attempted",
    "new_data_files_created",
    "existing_seed_files_modified",
    "network_executed",
    "trading_allowed",
    "real_orders_possible",
    "v1_95_execution_attempted",
    "available_ts_policy_defined",
    "decision_ts_policy_defined",
    "feature_available_ts_lte_decision_ts_rule_defined",
    "no_lookahead_policy_defined",
    "future_information_fields_forbidden",
    "target_like_fields_forbidden",
    "label_like_fields_forbidden",
    "prediction_like_fields_forbidden",
    "leakage_detected",
    "lookahead_detected",
    "forbidden_feature_terms_detected",
    "forbidden_feature_terms_count",
    "future_feature_dry_run_max_preview_rows",
    "future_feature_dry_run_max_theoretical_features",
    "release_ready_for_external_review",
    "clean_zip_ready_for_external_review",
    "smoke_test_passed",
    "blocking_reason",
]

EXPECTED_VALUES = {
    "version": V_DISP,
    "feature_readiness_pack_executed": True,
    "feature_schema_design_executed": True,
    "causal_feature_plan_created": True,
    "feature_dry_run_executed": True,
    "feature_dry_run_reports_only": True,
    "feature_dry_run_preview_created": True,
    "feature_dry_run_preview_in_reports_only": True,
    "approval_gate_only": True,
    "reports_only": True,
    "feature_generation_executed": False,
    "physical_features_created": False,
    "feature_files_created_in_data": False,
    "labels_created": False,
    "targets_created": False,
    "predictions_created": False,
    "model_training_executed": False,
    "ml_signal_validation_executed": False,
    "data_directory_write_attempted": False,
    "new_data_files_created": False,
    "existing_seed_files_modified": False,
    "network_executed": False,
    "trading_allowed": False,
    "real_orders_possible": False,
    "v1_95_execution_attempted": False,
    "available_ts_policy_defined": True,
    "decision_ts_policy_defined": True,
    "event_ts_policy_defined": True,
    "feature_available_ts_lte_decision_ts_rule_defined": True,
    "no_lookahead_policy_defined": True,
    "future_information_fields_forbidden": True,
    "target_like_fields_forbidden": True,
    "label_like_fields_forbidden": True,
    "prediction_like_fields_forbidden": True,
    "leakage_detected": False,
    "lookahead_detected": False,
    "forbidden_feature_terms_detected": False,
    "forbidden_feature_terms_count": 0,
    "release_ready_for_external_review": True,
    "clean_zip_ready_for_external_review": True,
    "smoke_test_passed": True,
    "blocking_reason": None,
}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _required_paths(version_suffix: str) -> dict[str, str]:
    return {
        "summary": f"reports/research/causal_feature_readiness_summary_{version_suffix}.json",
        "schema": f"reports/research/causal_feature_schema_design_{version_suffix}.json",
        "dryrun": f"reports/research/causal_feature_dryrun_preview_{version_suffix}.json",
        "anti_leakage": f"reports/research/causal_feature_anti_leakage_audit_{version_suffix}.json",
        "approval": f"reports/research/causal_feature_approval_decision_{version_suffix}.json",
        "safety": f"reports/research/causal_feature_readiness_safety_check_{version_suffix}.json",
        "consistency": f"reports/research/causal_feature_readiness_consistency_check_{version_suffix}.json",
        "latest": "reports/current/latest_metrics.json",
        "project": "reports/PROJECT_STATE.json",
        "index": "reports/REPORT_INDEX.md",
        "release": f"reports/release_zip_{version_suffix}.json",
        "audit": f"reports/zip_audit_{version_suffix}.json",
        "smoke": f"reports/zip_smoke_test_{version_suffix}.json",
        "code_review": f"docs/code_review_{version_suffix}.md",
        "doc": f"docs/causal_feature_readiness_{version_suffix}.md",
    }


def _validate_release_audit_smoke(
    release: dict[str, Any], audit: dict[str, Any], smoke: dict[str, Any]
) -> list[str]:
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
        "smoke_timeout_detected": False,
        "bounded_smoke_for_v1_94": True,
        "real_orders_possible": False,
        "codex_cli_called": False,
        "holdout_executed": False,
    }.items():
        if smoke.get(field) != expected:
            errors.append(f"smoke: {field} != {expected}")
    if smoke.get("smoke_passed_count") != smoke.get("smoke_commands_count"):
        errors.append("smoke: smoke_passed_count != smoke_commands_count")
    return errors


def _constant_value(node: ast.AST) -> Any:
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def _check_test_quality(root: Path) -> list[str]:
    errors: list[str] = []
    path = root / "tests/research/test_causal_feature_readiness_v1_94.py"
    if not path.exists():
        return errors
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                errors.append(f"pass-only test: {node.name}")
        if isinstance(node, ast.Assert):
            if isinstance(node.test, ast.Constant) and node.test.value is True:
                errors.append("assert True found")
            if isinstance(node.test, ast.Compare) and len(node.test.comparators) == 1:
                left = _constant_value(node.test.left)
                right = _constant_value(node.test.comparators[0])
                if left is not None and right is not None and type(node.test.ops[0]) in {ast.Eq, ast.Is} and left == right:
                    errors.append("tautological assertion found")
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
    latest = loaded["latest"]
    project = loaded["project"]

    for field, expected in EXPECTED_VALUES.items():
        if summary.get(field) != expected:
            errors.append(f"summary: {field} != {expected}")
    if (summary.get("future_feature_dry_run_max_preview_rows") or 0) > 10:
        errors.append("future_feature_dry_run_max_preview_rows > 10")
    if (summary.get("future_feature_dry_run_max_theoretical_features") or 0) > 20:
        errors.append("future_feature_dry_run_max_theoretical_features > 20")

    for field in SUMMARY_FIELDS:
        if field not in summary:
            errors.append(f"summary missing critical field {field}")
            continue
        for label, payload in [("latest", latest), ("project", project)]:
            if field not in payload:
                errors.append(f"{label} missing critical field {field}")
            elif payload[field] != summary[field]:
                errors.append(f"{label}: {field} diverges from summary")

    errors.extend(_validate_release_audit_smoke(loaded["release"], loaded["audit"], loaded["smoke"]))

    seed_audit = SeedReadinessReader(root).audit()
    if seed_audit["missing_seed_files_count"] != 0:
        errors.append("seed missing expected files")
    if seed_audit["unexpected_seed_files_count"] != 0:
        errors.append("seed has unexpected files")
    if seed_audit["seed_json_valid"] is not True:
        errors.append("seed JSON invalid")
    if seed_audit["seed_checksums_verified"] is not True:
        errors.append("seed checksums not verified")
    if seed_audit["seed_preview_records_count"] > 10:
        errors.append("seed preview records > 10")
    if seed_audit["seed_total_bytes_observed"] > 50000:
        errors.append("seed total bytes > 50000")
    seed_root = root / SEED_ROOT
    if seed_root.exists():
        existing = sorted(path.name for path in seed_root.glob("*") if path.is_file())
        if existing != sorted(EXPECTED_SEED_FILES):
            errors.append("seed files are not exact")

    schema = loaded["schema"]
    dryrun = loaded["dryrun"]
    scan = scan_forbidden_feature_terms(
        {
            "schema.theoretical_features": schema.get("theoretical_features", []),
            "dryrun.preview_rows": dryrun.get("preview_rows", []),
        }
    )
    if scan["forbidden_feature_terms_detected"]:
        errors.append(f"forbidden feature terms detected: {scan['forbidden_feature_term_occurrences']}")
    if loaded["anti_leakage"].get("forbidden_feature_terms_detected") is not False:
        errors.append("anti_leakage report declares forbidden terms")

    if schema.get("theoretical_features_count", 0) > 20:
        errors.append("schema theoretical_features_count > 20")
    if dryrun.get("preview_rows_count", 0) > 10:
        errors.append("dryrun preview rows > 10")
    if dryrun.get("feature_dry_run_data_write_allowed") is not False:
        errors.append("dryrun data write allowed")

    index = (root / "reports/REPORT_INDEX.md").read_text(encoding="utf-8")
    if "V1.94" not in index or "v1_94" not in index:
        errors.append("REPORT_INDEX does not reference V1.94")

    errors.extend(_check_test_quality(root))
    return errors
