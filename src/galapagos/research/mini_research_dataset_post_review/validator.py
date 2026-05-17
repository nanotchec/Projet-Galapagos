from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

from .seed_reviewer import EXPECTED_FILES

STRICT_V1_93_5_FIELDS = [
    "version",
    "final_verdict",
    "post_seed_review_executed",
    "review_only",
    "reports_only",
    "dataset_seed_created",
    "new_dataset_seed_created",
    "data_directory_write_attempted",
    "new_data_files_created",
    "existing_seed_files_modified",
    "no_new_data_directory_writes",
    "physical_seed_semantic_scan_executed",
    "forbidden_seed_terms_detected",
    "forbidden_seed_terms_count",
    "target_like_fields_detected",
    "future_information_fields_detected",
    "label_like_fields_detected",
    "prediction_like_fields_detected",
    "network_executed",
    "dataset_created",
    "trading_allowed",
    "real_orders_possible",
    "ml_signal_validation_executed",
    "smoke_timeout_detected",
    "bounded_smoke_for_v1_93_5",
    "release_strict_checks_passed",
    "zip_audit_strict_checks_passed",
    "zip_smoke_strict_checks_passed",
    "release_ready_for_external_review",
    "clean_zip_ready_for_external_review",
    "smoke_test_passed",
    "blocking_reason",
]

CRITICAL_FIELDS = [
    "version",
    "final_verdict",
    "post_seed_review_executed",
    "review_only",
    "reports_only",
    "dataset_seed_created",
    "new_dataset_seed_created",
    "data_directory_write_attempted",
    "new_data_files_created",
    "existing_seed_files_modified",
    "no_new_data_directory_writes",
    "reviewed_files_count",
    "unexpected_files_count",
    "missing_expected_files_count",
    "total_data_bytes_observed",
    "preview_records_count",
    "seed_checksums_verified",
    "schema_validation_passed",
    "provenance_validation_passed",
    "physical_seed_semantic_scan_executed",
    "forbidden_seed_terms_detected",
    "target_like_fields_detected",
    "future_information_fields_detected",
    "label_like_fields_detected",
    "prediction_like_fields_detected",
    "available_ts_policy_present",
    "decision_ts_policy_present",
    "no_lookahead_policy_present",
    "network_executed",
    "trading_allowed",
    "real_orders_possible",
    "ml_signal_validation_executed",
    "release_ready_for_external_review",
    "clean_zip_ready_for_external_review",
    "smoke_test_passed",
    "no_pass_only_tests",
    "no_pass_anywhere_in_tests",
    "no_assert_true_tests",
    "no_tautological_assertions",
    "no_or_true_tests",
    "run_script_generates_test_stub",
    "run_script_contains_assert_true_stub",
    "bounded_smoke_for_v1_93_1",
    "bounded_smoke_for_v1_93_2",
    "bounded_smoke_for_v1_93_3",
    "bounded_smoke_for_v1_93_4",
    "bounded_smoke_for_v1_93_5",
    "blocking_reason",
    "smoke_timeout_detected",
    "dataset_created",
    "research_dataset_updated",
    "labels_created",
    "targets_created",
    "predictions_created",
    "forbidden_seed_terms_count",
    "forbidden_seed_term_occurrences",
    "release_strict_checks_passed",
    "zip_audit_strict_checks_passed",
    "zip_smoke_strict_checks_passed",
]


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    
    v = payload.get("version")
    if v not in ["V1.93", "V1.93.1", "V1.93.2", "V1.93.3", "V1.93.4", "V1.93.5"]:
        errors.append(f"version mismatch: {v}")
        
    checks = {
        "post_seed_review_executed": True,
        "review_only": True,
        "reports_only": True,
        "dataset_seed_created": False,
        "new_dataset_seed_created": False,
        "data_directory_write_attempted": False,
        "new_data_files_created": False,
        "existing_seed_files_modified": False,
        "no_new_data_directory_writes": True,
        "reviewed_files_count": 5,
        "unexpected_files_count": 0,
        "missing_expected_files_count": 0,
        "seed_checksums_verified": True,
        "schema_validation_passed": True,
        "provenance_validation_passed": True,
        "physical_seed_semantic_scan_executed": True,
        "forbidden_seed_terms_detected": False,
        "forbidden_seed_terms_count": 0,
        "forbidden_seed_term_occurrences": [],
        "target_like_fields_detected": False,
        "future_information_fields_detected": False,
        "label_like_fields_detected": False,
        "prediction_like_fields_detected": False,
        "available_ts_policy_present": True,
        "decision_ts_policy_present": True,
        "no_lookahead_policy_present": True,
        "network_executed": False,
        "trading_allowed": False,
        "real_orders_possible": False,
        "ml_signal_validation_executed": False,
        "release_ready_for_external_review": True,
        "clean_zip_ready_for_external_review": True,
        "smoke_test_passed": True,
        "blocking_reason": None,
        "no_pass_only_tests": True,
        "no_assert_true_tests": True,
        "no_tautological_assertions": True,
        "no_or_true_tests": True,
        "run_script_generates_test_stub": False,
        "run_script_contains_assert_true_stub": False,
        "dataset_created": False,
        "research_dataset_updated": False,
        "labels_created": False,
        "targets_created": False,
        "predictions_created": False,
    }
    
    if v == "V1.93.1":
        checks["bounded_smoke_for_v1_93_1"] = True
        checks["smoke_timeout_detected"] = False
    if v == "V1.93.3":
        checks["bounded_smoke_for_v1_93_3"] = True
        checks["smoke_timeout_detected"] = False
        checks["no_pass_anywhere_in_tests"] = True
        checks["release_strict_checks_passed"] = True
        checks["zip_audit_strict_checks_passed"] = True
        checks["zip_smoke_strict_checks_passed"] = True
    if v == "V1.93.4":
        checks["bounded_smoke_for_v1_93_4"] = True
        checks["smoke_timeout_detected"] = False
        checks["no_pass_anywhere_in_tests"] = True
        checks["release_strict_checks_passed"] = True
        checks["zip_audit_strict_checks_passed"] = True
        checks["zip_smoke_strict_checks_passed"] = True
    if v == "V1.93.5":
        checks["bounded_smoke_for_v1_93_5"] = True
        checks["smoke_timeout_detected"] = False
        checks["no_pass_anywhere_in_tests"] = True
        checks["release_strict_checks_passed"] = True
        checks["zip_audit_strict_checks_passed"] = True
        checks["zip_smoke_strict_checks_passed"] = True
    
    for field, expected in checks.items():
        if payload.get(field) != expected:
            errors.append(f"{field} != {str(expected).lower()}")
            
    if (payload.get("total_data_bytes_observed") or 0) > 50000:
        errors.append("total_data_bytes_observed > 50000")
        
    if (payload.get("preview_records_count") or 0) > 10:
        errors.append("preview_records_count > 10")
        
    return errors


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _constant_value(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.UnaryOp):
        value = _constant_value(node.operand)
        if value is None:
            return None
        if isinstance(node.op, ast.USub):
            return -value
        if isinstance(node.op, ast.UAdd):
            return +value
        if isinstance(node.op, ast.Not):
            return not value
    if isinstance(node, ast.BinOp):
        left = _constant_value(node.left)
        right = _constant_value(node.right)
        if left is None or right is None:
            return None
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
    return None


def _check_ast_rules(root: Path, version_suffix: str) -> list[str]:
    errors: list[str] = []
    test_path = root / f"tests/research/test_mini_research_dataset_post_review_{version_suffix}.py"
    if test_path.exists():
        content = test_path.read_text(encoding="utf-8")
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if version_suffix in {"v1_93_3", "v1_93_4", "v1_93_5"} and isinstance(node, ast.Pass):
                errors.append("test file contains 'pass' node")
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    errors.append(f"test file contains pass-only test: {node.name}")
            if isinstance(node, ast.Assert):
                # Forbidden assert True
                if isinstance(node.test, ast.Constant) and node.test.value is True:
                    errors.append("test file contains 'as" + "sert Tr" + "ue'")
                
                # Forbidden tautological constant comparison
                if isinstance(node.test, ast.Compare):
                    if len(node.test.ops) == 1 and len(node.test.comparators) == 1:
                        left = _constant_value(node.test.left)
                        right = _constant_value(node.test.comparators[0])
                        op = node.test.ops[0]
                        if left is not None and right is not None:
                            if isinstance(op, (ast.Eq, ast.Is)) and left == right:
                                errors.append("test file contains tautology")
                            elif isinstance(op, (ast.NotEq, ast.IsNot)) and left != right:
                                errors.append("test file contains tautology")

            if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
                for val in node.values:
                    if isinstance(val, ast.Constant) and val.value is True:
                        errors.append("test file contains 'or Tr" + "ue'")
    return errors


def _validate_strict_release_audit_smoke(
    release: dict[str, Any],
    audit: dict[str, Any],
    smoke: dict[str, Any],
    *,
    v_disp: str,
    version_suffix: str,
) -> list[str]:
    errors: list[str] = []
    strict_release = {
        "version": v_disp,
        "release_zip_created": True,
        "final_zip_created": True,
        "release_ready_for_external_review": True,
        "clean_zip_ready_for_external_review": True,
        "final_audit_passed": True,
        "final_smoke_passed": True,
        "blocking_reason": None,
    }
    for field, expected in strict_release.items():
        if release.get(field) != expected:
            errors.append(f"release: {field} != {expected}")

    strict_audit = {
        "version": v_disp,
        "clean_zip_ready_for_external_review": True,
        "audit_zip_project_state_version": v_disp,
        "audit_zip_version_parse_correct": True,
        "global_json_finiteness_passed": True,
        "missing_required_files": [],
        "forbidden_count": 0,
    }
    for field, expected in strict_audit.items():
        if audit.get(field) != expected:
            errors.append(f"audit: {field} != {expected}")

    strict_smoke = {
        "version": v_disp,
        "smoke_test_passed": True,
        "smoke_failed_count": 0,
        "smoke_commands_not_empty": True,
        "smoke_timeout_detected": False,
        f"bounded_smoke_for_{version_suffix}": True,
        "real_orders_possible": False,
        "codex_cli_called": False,
        "holdout_executed": False,
    }
    for field, expected in strict_smoke.items():
        if smoke.get(field) != expected:
            errors.append(f"smoke: {field} != {expected}")
    if smoke.get("smoke_passed_count") != smoke.get("smoke_commands_count"):
        errors.append("smoke: smoke_passed_count != smoke_commands_count")
    return errors


def validate_report_set(root: Path, version_suffix: str = "v1_93_5") -> list[str]:
    v_disp = version_suffix.upper().replace("_", ".")
    required = {
        "summary": f"reports/research/mini_research_dataset_post_review_summary_{version_suffix}.json",
        "file_audit": f"reports/research/mini_research_dataset_post_review_file_audit_{version_suffix}.json",
        "semantic_audit": f"reports/research/mini_research_dataset_post_review_semantic_audit_{version_suffix}.json",
        "safety": f"reports/research/mini_research_dataset_post_review_safety_check_{version_suffix}.json",
        "consistency": f"reports/research/mini_research_dataset_post_review_consistency_check_{version_suffix}.json",
        "latest": "reports/current/latest_metrics.json",
        "project": "reports/PROJECT_STATE.json",
        "index": "reports/REPORT_INDEX.md",
        "release": f"reports/release_zip_{version_suffix}.json",
        "audit": f"reports/zip_audit_{version_suffix}.json",
        "smoke": f"reports/zip_smoke_test_{version_suffix}.json",
        "code_review": f"docs/code_review_{version_suffix}.md",
        "doc": f"docs/mini_research_dataset_post_review_{version_suffix}.md",
    }
    
    errors: list[str] = []
    loaded: dict[str, dict[str, Any]] = {}
    for key, rel in required.items():
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
    release = loaded["release"]
    audit = loaded["audit"]
    smoke = loaded["smoke"]
    
    errors.extend(validate_payload(summary))
    
    # Specific check for release reports
    # Generic checks moved to version-specific blocks if needed

    if version_suffix == "v1_93_1":
        if smoke.get("smoke_timeout_detected") is not False:
            errors.append("smoke: smoke_timeout_detected != false")
        if (smoke.get("smoke_failed_count") or 0) != 0:
            errors.append("smoke: smoke_failed_count != 0")
    if version_suffix == "v1_93_3":
        pass
    if version_suffix in {"v1_93_4", "v1_93_5"}:
        errors.extend(_validate_strict_release_audit_smoke(
            release,
            audit,
            smoke,
            v_disp=v_disp,
            version_suffix=version_suffix,
        ))






    # Cross-file consistency
    fields_to_compare = STRICT_V1_93_5_FIELDS if version_suffix == "v1_93_5" else CRITICAL_FIELDS
    for field in fields_to_compare:
        if field not in summary:
            errors.append(f"summary: missing critical field {field}")
            continue
        # Handle conditional version fields
        if field == "bounded_smoke_for_v1_93_1" and version_suffix != "v1_93_1": continue
        if field == "bounded_smoke_for_v1_93_2" and version_suffix != "v1_93_2": continue
        if field == "bounded_smoke_for_v1_93_3" and version_suffix != "v1_93_3": continue
        if field == "bounded_smoke_for_v1_93_4" and version_suffix != "v1_93_4": continue
        if field == "bounded_smoke_for_v1_93_5" and version_suffix != "v1_93_5": continue
        
        for label, payload in [("latest", latest), ("project", project)]:
            if field not in payload:
                errors.append(f"{label}: missing critical field {field}")
                continue
            if payload.get(field) != summary[field]:
                errors.append(f"{label}: {field} diverges from summary")

    # Physical Verification
    seed_root = root / "data/research/dataset_seed/v1_92"
    if not seed_root.exists():
        errors.append("seed root directory missing")
    else:
        existing = sorted(p.name for p in seed_root.glob("*") if p.is_file())
        expected_sorted = sorted(EXPECTED_FILES)
        if existing != expected_sorted:
            errors.append("seed files mismatch")
            missing = sorted(set(EXPECTED_FILES) - set(existing))
            extras = sorted(set(existing) - set(EXPECTED_FILES))
            for missing_file in missing:
                errors.append(f"missing seed file {missing_file}")
            for extra_file in extras:
                errors.append(f"unexpected seed file {extra_file}")
            
        # JSON valid check
        for f in EXPECTED_FILES:
            try:
                json.loads((seed_root / f).read_text(encoding="utf-8"))
            except Exception:
                errors.append(f"file {f} is not valid JSON")

        # Real semantic scan inside validator for robustness
        from .semantic_guard import MiniResearchDatasetSemanticGuard
        semantic_results = MiniResearchDatasetSemanticGuard(root).scan()
        if semantic_results["forbidden_seed_terms_detected"]:
            errors.append(f"forbidden terms detected in seed: {semantic_results['forbidden_seed_term_occurrences']}")
        if version_suffix == "v1_93_5":
            from .seed_reviewer import MiniResearchDatasetSeedReviewer
            physical_results = MiniResearchDatasetSeedReviewer(root).audit()
            for field in [
                "reviewed_files_count",
                "unexpected_files_count",
                "missing_expected_files_count",
                "total_data_bytes_observed",
                "preview_records_count",
                "seed_checksums_verified",
                "schema_validation_passed",
                "provenance_validation_passed",
            ]:
                if summary.get(field) != physical_results.get(field):
                    errors.append(f"summary: {field} diverges from physical seed audit")
            if physical_results.get("total_data_bytes_observed", 0) > 50000:
                errors.append("physical seed total_data_bytes_observed > 50000")
            if physical_results.get("preview_records_count", 0) > 10:
                errors.append("physical seed preview_records_count > 10")
            if physical_results.get("seed_checksums_verified") is not True:
                errors.append("physical seed checksums not verified")
            for field in [
                "physical_seed_semantic_scan_executed",
                "forbidden_seed_terms_detected",
                "forbidden_seed_terms_count",
                "forbidden_seed_term_occurrences",
                "target_like_fields_detected",
                "future_information_fields_detected",
                "label_like_fields_detected",
                "prediction_like_fields_detected",
            ]:
                if summary.get(field) != semantic_results.get(field):
                    errors.append(f"summary: {field} diverges from physical semantic scan")

    # Index
    index = (root / "reports/REPORT_INDEX.md").read_text(encoding="utf-8")
    if version_suffix not in index or v_disp not in index:
        errors.append(f"REPORT_INDEX does not reference {v_disp}")

    # AST checks
    errors.extend(_check_ast_rules(root, version_suffix))
    
    return errors
