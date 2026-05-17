from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

from .approval_gate import EXPECTED_FUTURE_SCOPE
from .physical_auditor import MiniResearchDatasetPhysicalAuditor
from .safety_guard import MiniResearchDatasetReadinessSafetyGuard

CRITICAL_FIELDS = [
    "version",
    "final_verdict",
    "post_consolidation_review_executed",
    "dataset_seed_design_executed",
    "anti_leakage_plan_created",
    "approval_gate_only",
    "reports_only",
    "dataset_seed_created",
    "dataset_created",
    "data_directory_write_attempted",
    "new_data_files_created",
    "existing_data_files_modified",
    "existing_v1_84_files_modified",
    "existing_v1_87_files_modified",
    "existing_v1_90_files_modified",
    "no_new_data_directory_writes",
    "network_executed",
    "trading_allowed",
    "real_orders_possible",
    "ml_signal_validation_executed",
    "v1_92_execution_attempted",
    "human_approval_granted",
    "approval_phrase_match",
    "v1_92_authorized",
    "authorized_future_scope",
    "dataset_seed_design_created",
    "future_dataset_seed_allowed_root",
    "future_dataset_seed_max_files",
    "future_dataset_seed_max_bytes",
    "available_ts_policy_defined",
    "feature_available_ts_lte_decision_ts_rule_defined",
    "no_lookahead_policy_defined",
    "provenance_policy_defined",
    "release_ready_for_external_review",
    "clean_zip_ready_for_external_review",
    "smoke_test_passed",
    "blocking_reason",
    "no_pass_only_tests",
    "no_assert_true_tests",
    "no_or_true_tests",
    "run_script_generates_test_stub",
    "run_script_contains_assert_true_stub",
    "no_tautological_assertions",
    "bounded_smoke_for_v1_91_3",
    "smoke_timeout_detected",
]


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors = MiniResearchDatasetReadinessSafetyGuard().check(payload)["safety_issues"]
    if payload.get("approval_phrase_match") is False and payload.get("human_approval_granted") is True:
        errors.append("human_approval_granted true with phrase mismatch")
    if payload.get("human_approval_granted") is True:
        if payload.get("authorized_future_version") != "V1.92":
            errors.append("authorized_future_version != V1.92")
        if payload.get("authorized_future_scope") != EXPECTED_FUTURE_SCOPE:
            errors.append("authorized_future_scope mismatch")
    if payload.get("release_ready_for_external_review") is not True:
        errors.append("release_ready_for_external_review != true")
    if payload.get("smoke_test_passed") is not True:
        errors.append("smoke_test_passed != true")
    if payload.get("clean_zip_ready_for_external_review") is not True:
        errors.append("clean_zip_ready_for_external_review != true")
    
    v = payload.get("version")
    if v in {"V1.91.2", "V1.91.3", "V1.91.4"}:
        if payload.get("no_pass_only_tests") is not True:
            errors.append("no_pass_only_tests != true")
        if payload.get("no_assert_true_tests") is not True:
            errors.append("no_assert_true_tests != true")
        if payload.get("no_or_true_tests") is not True:
            errors.append("no_or_true_tests != true")
        if payload.get("run_script_generates_test_stub") is not False:
            errors.append("run_script_generates_test_stub != false")
        if payload.get("run_script_contains_assert_true_stub") is not False:
            errors.append("run_script_contains_assert_true_stub != false")
    
    if v in {"V1.91.3", "V1.91.4"}:
        if payload.get("no_tautological_assertions") is not True:
            errors.append("no_tautological_assertions != true")
        
    if v == "V1.91.3":
        if payload.get("bounded_smoke_for_v1_91_3") is not True:
            errors.append("bounded_smoke_for_v1_91_3 != true")
        if payload.get("smoke_timeout_detected") is not False:
            errors.append("smoke_timeout_detected != false")

    if v == "V1.91.4":
        if payload.get("bounded_smoke_for_v1_91_4") is not True:
            errors.append("bounded_smoke_for_v1_91_4 != true")

    return errors


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _is_trivial_const(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant)


def _check_ast_rules(root: Path, version_suffix: str) -> list[str]:
    errors: list[str] = []
    test_path = root / f"tests/research/test_mini_research_dataset_readiness_{version_suffix}.py"
    run_path = root / f"scripts/run_mini_research_dataset_readiness_{version_suffix}.py"
    
    if version_suffix in {"v1_91_2", "v1_91_3", "v1_91_4"}:
        if test_path.exists():
            content = test_path.read_text(encoding="utf-8")
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                        errors.append(f"test file contains pass-only test: {node.name}")
                if isinstance(node, ast.Assert):
                    # assert True
                    if isinstance(node.test, ast.Constant) and node.test.value is True:
                        errors.append("test file contains 'assert True'")
                    
                    if version_suffix in {"v1_91_3", "v1_91_4"}:
                        # Tautological assertions: 1 == 1, "x" == "x"
                        if isinstance(node.test, ast.Compare):
                            if len(node.test.ops) == 1 and len(node.test.comparators) == 1:
                                left = node.test.left
                                right = node.test.comparators[0]
                                op = node.test.ops[0]
                                if _is_trivial_const(left) and _is_trivial_const(right):
                                    lv = left.value
                                    rv = right.value
                                    if isinstance(op, (ast.Eq, ast.Is)):
                                        if lv == rv:
                                            errors.append(f"test file contains tautology: {lv} {type(op).__name__} {rv}")
                                    elif isinstance(op, (ast.NotEq, ast.IsNot)):
                                        if lv != rv:
                                            errors.append(f"test file contains tautology: {lv} {type(op).__name__} {rv}")

                if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
                    for val in node.values:
                        if isinstance(val, ast.Constant) and val.value is True:
                            errors.append("test file contains 'or True'")
        
        if run_path.exists():
            content = run_path.read_text(encoding="utf-8")
            if "assert True" in content:
                errors.append("run script contains 'assert True'")
            if "def test_stub" in content:
                errors.append("run script contains 'def test_stub'")
            if "test_stub" in content:
                errors.append("run script contains 'test_stub'")
            if version_suffix in {"v1_91_3", "v1_91_4"}:
                if "True is not False" in content:
                    errors.append("run script contains 'True is not False'")
            
    return errors


def validate_report_set(root: Path, version_suffix: str = "v1_91_3") -> list[str]:
    v_disp = version_suffix.upper().replace("_", ".")
    required = {
        "summary": f"reports/research/mini_research_dataset_readiness_summary_{version_suffix}.json",
        "physical": f"reports/research/mini_research_dataset_readiness_physical_audit_{version_suffix}.json",
        "design": f"reports/research/mini_research_dataset_seed_design_{version_suffix}.json",
        "anti": f"reports/research/mini_research_dataset_anti_leakage_plan_{version_suffix}.json",
        "approval": f"reports/research/mini_research_dataset_approval_decision_{version_suffix}.json",
        "safety": f"reports/research/mini_research_dataset_readiness_safety_check_{version_suffix}.json",
        "consistency": f"reports/research/mini_research_dataset_readiness_consistency_check_{version_suffix}.json",
        "latest": "reports/current/latest_metrics.json",
        "project": "reports/PROJECT_STATE.json",
        "index": "reports/REPORT_INDEX.md",
        "release": f"reports/release_zip_{version_suffix}.json",
        "audit": f"reports/zip_audit_{version_suffix}.json",
        "smoke": f"reports/zip_smoke_test_{version_suffix}.json",
        "code_review": f"docs/code_review_{version_suffix}.md",
        "doc": f"docs/mini_research_dataset_readiness_{version_suffix}.md",
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
            if not path.with_suffix(".md").exists() and key in {"summary", "physical", "design", "anti", "approval", "safety", "consistency", "release", "audit", "smoke"}:
                errors.append(f"missing markdown {path.with_suffix('.md').relative_to(root)}")
    if errors:
        return errors
    
    summary = loaded["summary"]
    latest = loaded["latest"]
    project = loaded["project"]
    design = loaded["design"]
    anti = loaded["anti"]
    release = loaded["release"]
    audit = loaded["audit"]
    smoke = loaded["smoke"]

    errors.extend(validate_payload(summary))
    
    # Specific checks for smoke report in V1.91.3
    if version_suffix == "v1_91_3":
        if smoke.get("smoke_timeout_detected") is not False:
            errors.append("smoke: smoke_timeout_detected != false")
        if (smoke.get("smoke_failed_count") or 0) != 0:
            errors.append("smoke: smoke_failed_count != 0")

    # Specific checks for smoke report in V1.91.4
    if version_suffix == "v1_91_4":
        if smoke.get("smoke_timeout_detected") is not False:
            errors.append("smoke: smoke_timeout_detected != false")
        if (smoke.get("smoke_failed_count") or 0) != 0:
            errors.append("smoke: smoke_failed_count != 0")
        if smoke.get("smoke_test_passed") is not True:
            errors.append("smoke: smoke_test_passed != true")
        if smoke.get("smoke_runs_full_pytest_suite") is not False:
            errors.append("smoke: smoke_runs_full_pytest_suite != false")
        if smoke.get("smoke_calls_smoke_script") is not False:
            errors.append("smoke: smoke_calls_smoke_script != false")
        if smoke.get("smoke_runs_audit_clean_zip_full_scan") is not False:
            errors.append("smoke: smoke_runs_audit_clean_zip_full_scan != false")

    
    # Cross-file consistency
    for field in CRITICAL_FIELDS:
        if field == "bounded_smoke_for_v1_91_3" and version_suffix != "v1_91_3":
            continue
        if field == "bounded_smoke_for_v1_91_4" and version_suffix != "v1_91_4":
            continue
        
        for label, payload in [("summary", summary), ("latest", latest), ("project", project)]:
            if field not in payload:
                errors.append(f"{label} missing critical field {field}")
        if field in summary and latest.get(field) != summary.get(field):
            errors.append(f"latest: {field} diverges from summary")
        if field in summary and project.get(field) != summary.get(field):
            errors.append(f"project: {field} diverges from summary")

    # Dataset Seed Design Strict Checks
    if design.get("dataset_seed_design_created") is not True:
        errors.append("design: dataset_seed_design_created != true")
    if design.get("dataset_seed_plan_reports_only") is not True:
        errors.append("design: dataset_seed_plan_reports_only != true")
    if design.get("dataset_seed_plan_theoretical_paths_only") is not True:
        errors.append("design: dataset_seed_plan_theoretical_paths_only != true")
    if design.get("future_dataset_seed_requires_v1_91_approval") is not True:
        errors.append("design: future_dataset_seed_requires_v1_91_approval != true")
    if design.get("future_dataset_seed_allowed_root") != "data/research/dataset_seed/v1_92/":
        errors.append("design: future_dataset_seed_allowed_root mismatch")
    if (design.get("future_dataset_seed_max_files") or 0) > 5:
        errors.append("design: future_dataset_seed_max_files > 5")
    if (design.get("future_dataset_seed_max_bytes") or 0) > 50000:
        errors.append("design: future_dataset_seed_max_bytes > 50000")
    if design.get("future_dataset_seed_allowed_extensions") != [".json"]:
        errors.append("design: future_dataset_seed_allowed_extensions != ['.json']")
    
    forbidden = [".parquet", ".csv", ".sqlite", ".jsonl", ".db"]
    for ext in forbidden:
        if ext not in (design.get("future_dataset_seed_forbidden_extensions") or []):
            errors.append(f"design: {ext} not in future_dataset_seed_forbidden_extensions")
    
    for field in ["future_dataset_seed_no_network", "future_dataset_seed_no_ml", "future_dataset_seed_no_trading", "future_dataset_seed_no_full_dataset"]:
        if design.get(field) is not True:
            errors.append(f"design: {field} != true")
    if (design.get("future_dataset_rows_preview_limit") or 0) > 10:
        errors.append("design: future_dataset_rows_preview_limit > 10")
    
    targets = design.get("target_files_theoretical") or []
    if not targets:
        errors.append("design: target_files_theoretical is empty")
    for t in targets:
        if not t.startswith("data/research/dataset_seed/v1_92/"):
            errors.append(f"design: target {t} outside allowed root")
        if not t.endswith(".json"):
            errors.append(f"design: target {t} has non-json extension")

    # Anti-Leakage Plan Strict Checks
    if anti.get("anti_leakage_plan_created") is not True:
        errors.append("anti: anti_leakage_plan_created != true")
    for field in [
        "causal_timestamp_policy_defined", "available_ts_policy_defined", 
        "event_ts_policy_defined", "decision_ts_policy_defined",
        "feature_available_ts_lte_decision_ts_rule_defined", "no_lookahead_policy_defined",
        "provenance_policy_defined", "manifest_checksum_policy_defined", "schema_validation_policy_defined"
    ]:
        if anti.get(field) is not True:
            errors.append(f"anti: {field} != true")
    if (anti.get("future_dataset_rows_preview_limit") or 0) > 10:
        errors.append("anti: future_dataset_rows_preview_limit > 10")
    
    rules = anti.get("anti_leakage_rules") or []
    if not rules:
        errors.append("anti: anti_leakage_rules is empty")
    rules_text = " ".join(rules).lower()
    if "available_ts" not in rules_text:
        errors.append("anti: available_ts missing from rules")
    if "decision_ts" not in rules_text:
        errors.append("anti: decision_ts missing from rules")
    if "lookahead" not in rules_text:
        errors.append("anti: lookahead missing from rules")

    # Release Strict Checks
    if release.get("version") != v_disp:
        errors.append(f"release: version mismatch {release.get('version')} != {v_disp}")
    for field in ["release_zip_created", "final_zip_created", "release_ready_for_external_review", "clean_zip_ready_for_external_review", "final_audit_passed", "final_smoke_passed"]:
        if release.get(field) is not True:
            errors.append(f"release: {field} != true")
    if release.get("blocking_reason") is not None:
        errors.append("release: blocking_reason is not None")

    # ZIP Audit Strict Checks
    if audit.get("version") != v_disp:
        errors.append(f"audit: version mismatch {audit.get('version')} != {v_disp}")
    if audit.get("clean_zip_ready_for_external_review") is not True:
        errors.append("audit: clean_zip_ready_for_external_review != true")
    if audit.get("audit_zip_project_state_version") != v_disp:
        errors.append(f"audit: project state version mismatch {audit.get('audit_zip_project_state_version')} != {v_disp}")
    if audit.get("audit_zip_version_parse_correct") is not True:
        errors.append("audit: audit_zip_version_parse_correct != true")
    if audit.get("global_json_finiteness_passed") is not True:
        errors.append("audit: global_json_finiteness_passed != true")
    if audit.get("missing_required_files") != []:
        errors.append("audit: missing_required_files is not empty")
    if audit.get("forbidden_count") != 0:
        errors.append("audit: forbidden_count != 0")

    # ZIP Smoke Strict Checks
    if smoke.get("version") != v_disp:
        errors.append(f"smoke: version mismatch {smoke.get('version')} != {v_disp}")
    if smoke.get("smoke_test_passed") is not True:
        errors.append("smoke: smoke_test_passed != true")
    if smoke.get("smoke_failed_count") != 0:
        errors.append("smoke: smoke_failed_count != 0")
    if smoke.get("smoke_passed_count") != smoke.get("smoke_commands_count"):
        errors.append("smoke: smoke_passed_count mismatch")
    if smoke.get("smoke_commands_not_empty") is not True:
        errors.append("smoke: smoke_commands_not_empty != true")
    for field in ["real_orders_possible", "codex_cli_called", "holdout_executed"]:
        if smoke.get(field) is not False:
            errors.append(f"smoke: {field} != false")

    # Physical Audit
    physical = MiniResearchDatasetPhysicalAuditor(root).audit()
    for field in ["v1_84_hashes_verified", "v1_87_hashes_verified", "v1_90_hashes_verified"]:
        if physical[field] is not True:
            errors.append(f"physical: {field} != true")
    for field in ["v1_84_unexpected_files_count", "v1_87_unexpected_files_count", "v1_90_unexpected_files_count"]:
        if physical[field] != 0:
            errors.append(f"physical: {field} != 0")
    if physical["v1_90_hashes_observed"] != loaded["physical"].get("v1_90_hashes_observed"):
        errors.append("physical_audit: V1.90 hashes do not match files")
    
    # Extra data check
    if (root / "data/research/dataset_seed/v1_92/").exists():
        errors.append(f"physical: data/research/dataset_seed/v1_92/ directory exists (forbidden in {v_disp})")

    # AST checks
    errors.extend(_check_ast_rules(root, version_suffix))

    # Index
    index = (root / "reports/REPORT_INDEX.md").read_text(encoding="utf-8")
    if version_suffix not in index or v_disp not in index:
        errors.append(f"REPORT_INDEX does not reference {v_disp}")
    
    return errors
