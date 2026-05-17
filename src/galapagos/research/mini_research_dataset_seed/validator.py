from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

from .physical_auditor import V1_92_FILES, MiniResearchDatasetSeedPhysicalAuditor, sha256_file
from .safety_guard import MiniResearchDatasetSeedSafetyGuard
from .semantic_scan import scan_physical_seed_semantics
from .seed_builder import AUTHORIZED_SCOPE

CRITICAL_FIELDS = [
    "version",
    "final_verdict",
    "approval_source_verified",
    "human_approval_granted",
    "approval_phrase_match",
    "v1_92_authorized",
    "dataset_seed_created",
    "mini_research_dataset_seed_only",
    "full_dataset_created",
    "data_directory_writes_allowed",
    "data_write_approved",
    "data_directory_write_attempted",
    "new_data_files_created",
    "dataset_seed_actual_write_executed",
    "unapproved_data_write_detected",
    "total_new_data_files_created",
    "created_files_count",
    "total_data_bytes_written",
    "preview_records_count",
    "existing_v1_84_files_modified",
    "existing_v1_87_files_modified",
    "existing_v1_90_files_modified",
    "parquet_created",
    "csv_created",
    "sqlite_created",
    "jsonl_created",
    "db_created",
    "dataset_created",
    "research_dataset_updated",
    "labels_created",
    "targets_created",
    "predictions_created",
    "ml_signal_validation_executed",
    "feature_generation_executed",
    "model_training_executed",
    "anti_leakage_plan_applied",
    "available_ts_policy_applied",
    "feature_available_ts_lte_decision_ts_rule_applied",
    "no_lookahead_policy_applied",
    "leakage_detected",
    "future_information_fields_detected",
    "forbidden_target_like_fields_detected",
    "physical_seed_semantic_scan_executed",
    "forbidden_seed_terms_detected",
    "forbidden_seed_terms_count",
    "forbidden_seed_term_occurrences",
    "target_like_fields_detected",
    "label_like_fields_detected",
    "prediction_like_fields_detected",
    "network_executed",
    "trading_allowed",
    "real_orders_possible",
    "release_ready_for_external_review",
    "clean_zip_ready_for_external_review",
    "smoke_test_passed",
    "blocking_reason",
]


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors = MiniResearchDatasetSeedSafetyGuard().check(payload)["safety_issues"]
    if payload.get("authorized_future_scope") != AUTHORIZED_SCOPE:
        errors.append("authorized_future_scope mismatch")
    if payload.get("total_data_bytes_written", 999_999) > 50_000:
        errors.append("total_data_bytes_written > 50000")
    if payload.get("preview_records_count", 99) > 10:
        errors.append("preview_records_count > 10")
    for field in [
        "labels_created",
        "targets_created",
        "predictions_created",
        "ml_signal_validation_executed",
        "feature_generation_executed",
        "model_training_executed",
        "leakage_detected",
        "lookahead_detected",
        "future_information_fields_detected",
        "forbidden_target_like_fields_detected",
        "network_executed",
        "trading_allowed",
        "real_orders_possible",
    ]:
        if payload.get(field) is not False:
            errors.append(f"{field} != false")
    for field in [
        "release_ready_for_external_review",
        "smoke_test_passed",
        "clean_zip_ready_for_external_review",
    ]:
        if payload.get(field) is not True:
            errors.append(f"{field} != true")
    return errors


def validate_report_set(root: Path, version_suffix: str = "v1_92") -> list[str]:
    if version_suffix not in {"v1_92", "v1_92_1"}:
        return [f"unsupported version {version_suffix}"]
    doc_name = "mini_research_dataset_seed_v1_92.md" if version_suffix == "v1_92" else "mini_research_dataset_seed_v1_92_1.md"
    required = {
        "summary": f"reports/research/mini_research_dataset_seed_summary_{version_suffix}.json",
        "file_audit": f"reports/research/mini_research_dataset_seed_file_audit_{version_suffix}.json",
        "anti": f"reports/research/mini_research_dataset_seed_anti_leakage_audit_{version_suffix}.json",
        "semantic": f"reports/research/mini_research_dataset_seed_semantic_scan_{version_suffix}.json",
        "safety": f"reports/research/mini_research_dataset_seed_safety_check_{version_suffix}.json",
        "consistency": f"reports/research/mini_research_dataset_seed_consistency_check_{version_suffix}.json",
        "latest": "reports/current/latest_metrics.json",
        "project": "reports/PROJECT_STATE.json",
        "index": "reports/REPORT_INDEX.md",
        "release": f"reports/release_zip_{version_suffix}.json",
        "audit": f"reports/zip_audit_{version_suffix}.json",
        "smoke": f"reports/zip_smoke_test_{version_suffix}.json",
        "code_review": f"docs/code_review_{version_suffix}.md",
        "doc": f"docs/{doc_name}",
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
            if key in {"summary", "file_audit", "anti", "semantic", "safety", "consistency", "release", "audit", "smoke"}:
                if not path.with_suffix(".md").exists():
                    errors.append(f"missing markdown {path.with_suffix('.md').relative_to(root)}")
    if errors:
        return errors

    summary = loaded["summary"]
    latest = loaded["latest"]
    project = loaded["project"]
    file_audit = loaded["file_audit"]
    anti = loaded["anti"]
    semantic = loaded["semantic"]
    release = loaded["release"]
    audit = loaded["audit"]
    smoke = loaded["smoke"]

    errors.extend(validate_payload(summary))
    errors.extend(_validate_release_audit_smoke(release, audit, smoke))
    errors.extend(_validate_cross_file(summary, latest, project))
    errors.extend(_validate_file_audit(file_audit))
    errors.extend(_validate_anti_leakage(anti))
    errors.extend(_validate_semantic_scan(semantic))
    errors.extend(_validate_physical_outputs(root, file_audit, semantic))
    errors.extend(_validate_index_and_docs(root, version_suffix))
    errors.extend(_check_ast_rules(root, version_suffix))
    return errors


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_release_audit_smoke(
    release: dict[str, Any], audit: dict[str, Any], smoke: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    for field in ["release_zip_created", "final_zip_created", "release_ready_for_external_review", "clean_zip_ready_for_external_review", "final_audit_passed", "final_smoke_passed"]:
        if release.get(field) is not True:
            errors.append(f"release: {field} != true")
    if release.get("blocking_reason") is not None:
        errors.append("release: blocking_reason != null")
    if release.get("version") not in {"V1.92", "V1.92.1"}:
        errors.append("release: version mismatch")
    if audit.get("audit_zip_project_state_version") != release.get("version"):
        errors.append("audit: audit_zip_project_state_version mismatch")
    if audit.get("audit_zip_version_parse_correct") is not True:
        errors.append("audit: audit_zip_version_parse_correct != true")
    if audit.get("forbidden_count") != 0:
        errors.append("audit: forbidden_count != 0")
    if audit.get("missing_required_files") != []:
        errors.append("audit: missing_required_files != []")
    if audit.get("global_json_finiteness_passed") is not True:
        errors.append("audit: global_json_finiteness_passed != true")
    if smoke.get("smoke_test_passed") is not True:
        errors.append("smoke: smoke_test_passed != true")
    if smoke.get("smoke_failed_count") != 0:
        errors.append("smoke: smoke_failed_count != 0")
    if smoke.get("smoke_passed_count") != smoke.get("smoke_commands_count"):
        errors.append("smoke: smoke_passed_count mismatch")
    if smoke.get("smoke_commands_not_empty") is not True:
        errors.append("smoke: smoke_commands_not_empty != true")
    return errors


def _validate_cross_file(
    summary: dict[str, Any], latest: dict[str, Any], project: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    for field in CRITICAL_FIELDS:
        for label, payload in [("summary", summary), ("latest", latest), ("project", project)]:
            if field not in payload:
                errors.append(f"{label} missing critical field {field}")
        if field in summary and latest.get(field) != summary.get(field):
            errors.append(f"latest: {field} diverges from summary")
        if field in summary and project.get(field) != summary.get(field):
            errors.append(f"project: {field} diverges from summary")
    return errors


def _validate_file_audit(file_audit: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ["seed_manifest_json_created", "seed_schema_json_created", "seed_preview_records_json_created", "seed_provenance_json_created", "seed_quality_audit_json_created", "seed_json_valid"]:
        if file_audit.get(field) is not True:
            errors.append(f"file_audit: {field} != true")
    for field in ["unapproved_data_write_detected", "existing_v1_84_files_modified", "existing_v1_87_files_modified", "existing_v1_90_files_modified", "parquet_created", "csv_created", "sqlite_created", "jsonl_created", "db_created"]:
        if file_audit.get(field) is not False:
            errors.append(f"file_audit: {field} != false")
    if file_audit.get("created_files_count") != 5:
        errors.append("file_audit: created_files_count != 5")
    if file_audit.get("total_new_data_files_created") != 5:
        errors.append("file_audit: total_new_data_files_created != 5")
    if file_audit.get("total_data_bytes_written", 999_999) > 50_000:
        errors.append("file_audit: total_data_bytes_written > 50000")
    if file_audit.get("preview_records_count", 99) > 10:
        errors.append("file_audit: preview_records_count > 10")
    return errors


def _validate_anti_leakage(anti: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ["anti_leakage_plan_applied", "available_ts_policy_applied", "feature_available_ts_lte_decision_ts_rule_applied", "no_lookahead_policy_applied", "provenance_policy_applied", "manifest_checksum_policy_applied", "schema_validation_policy_applied"]:
        if anti.get(field) is not True:
            errors.append(f"anti: {field} != true")
    for field in ["leakage_detected", "lookahead_detected", "future_information_fields_detected", "forbidden_target_like_fields_detected"]:
        if anti.get(field) is not False:
            errors.append(f"anti: {field} != false")
    return errors


def _validate_semantic_scan(semantic: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ["physical_seed_semantic_scan_executed"]:
        if semantic.get(field) is not True:
            errors.append(f"semantic: {field} != true")
    for field in [
        "forbidden_seed_terms_detected",
        "target_like_fields_detected",
        "future_information_fields_detected",
        "label_like_fields_detected",
        "prediction_like_fields_detected",
    ]:
        if semantic.get(field) is not False:
            errors.append(f"semantic: {field} != false")
    if semantic.get("forbidden_seed_terms_count") != 0:
        errors.append("semantic: forbidden_seed_terms_count != 0")
    if semantic.get("forbidden_seed_term_occurrences") != []:
        errors.append("semantic: forbidden_seed_term_occurrences != []")
    return errors


def _validate_physical_outputs(root: Path, file_audit: dict[str, Any], semantic_report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    auditor = MiniResearchDatasetSeedPhysicalAuditor(root)
    physical = auditor.audit_seed_outputs()
    if set(physical["created_file_paths"]) != {str(path) for path in V1_92_FILES}:
        errors.append("physical: V1.92 folder does not contain exactly the five authorized JSON files")
    for rel in V1_92_FILES:
        path = root / rel
        if not path.exists():
            errors.append(f"physical: missing {rel}")
        elif path.suffix.lower() != ".json":
            errors.append(f"physical: non-json V1.92 file {rel}")
    if physical["unapproved_data_write_detected"]:
        errors.append("physical: unapproved V1.92 data write detected")
    if physical["total_data_bytes_written"] > 50_000:
        errors.append("physical: total_data_bytes_written > 50000")
    if physical["preview_records_count"] > 10:
        errors.append("physical: preview_records_count > 10")
    if not _declared_seed_checksums_match(root):
        errors.append("physical: declared seed checksums do not match files")
    semantic = scan_physical_seed_semantics(root)
    if semantic.get("forbidden_seed_terms_detected") is not False:
        errors.append(f"physical: forbidden seed terms detected {semantic.get('forbidden_seed_term_occurrences')}")
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
        if semantic_report.get(field) != semantic.get(field):
            errors.append(f"semantic: {field} diverges from physical scan")
    for key in ["v1_84_hashes_observed", "v1_87_hashes_observed", "v1_90_hashes_observed"]:
        if key in file_audit and file_audit[key] != physical[key]:
            errors.append(f"physical: {key} diverges from file_audit")
    return errors


def _declared_seed_checksums_match(root: Path) -> bool:
    manifest_path = root / V1_92_FILES[0]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    checksums = manifest.get("seed_file_checksums")
    if not isinstance(checksums, dict):
        return False
    for rel in V1_92_FILES[1:]:
        if checksums.get(rel.name) != sha256_file(root / rel):
            return False
    return True


def _validate_index_and_docs(root: Path, version_suffix: str) -> list[str]:
    errors: list[str] = []
    display = version_suffix.upper().replace("_", ".")
    index = (root / "reports/REPORT_INDEX.md").read_text(encoding="utf-8")
    if version_suffix not in index or display not in index:
        errors.append(f"REPORT_INDEX does not reference {display}")
    latest_summary = (root / "reports/current/latest_summary.md").read_text(encoding="utf-8")
    if display not in latest_summary:
        errors.append(f"latest_summary does not mention {display}")
    return errors


def _check_ast_rules(root: Path, version_suffix: str) -> list[str]:
    errors: list[str] = []
    test_path = root / f"tests/research/test_mini_research_dataset_seed_{version_suffix}.py"
    if not test_path.exists():
        return errors
    tree = ast.parse(test_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                errors.append(f"test file contains pass-only test: {node.name}")
        if isinstance(node, ast.Assert):
            if isinstance(node.test, ast.Constant) and node.test.value is True:
                errors.append("test file contains 'assert True'")
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
            if any(isinstance(value, ast.Constant) and value.value is True for value in node.values):
                errors.append("test file contains 'or True'")
    return errors
