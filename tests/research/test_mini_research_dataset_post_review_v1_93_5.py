from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pytest

from galapagos.research.mini_research_dataset_post_review.validator import validate_report_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]
VERSION = "V1.93.5"
VERSION_SUFFIX = "v1_93_5"
SEED_ROOT = Path("data/research/dataset_seed/v1_92")
SEED_FILES = [
    "seed_manifest.json",
    "seed_schema.json",
    "seed_preview_records.json",
    "seed_provenance.json",
    "seed_quality_audit.json",
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _seed_payloads() -> dict[str, dict]:
    return {
        "seed_schema.json": {
            "fields": [
                {"name": "available_ts", "type": "string"},
                {"name": "decision_ts", "type": "string"},
                {"name": "source_version", "type": "string"},
            ],
            "policies": ["available_ts <= decision_ts", "no_lookahead"],
        },
        "seed_preview_records.json": {
            "records": [
                {
                    "available_ts": "2026-01-01T00:00:00Z",
                    "decision_ts": "2026-01-01T00:00:00Z",
                    "source_version": "V1.92.1",
                }
            ]
        },
        "seed_provenance.json": {"sources": ["V1.84", "V1.87.2", "V1.90.1"], "decision_ts": "present"},
        "seed_quality_audit.json": {"available_ts_policy": "present", "no_lookahead_policy": "present"},
    }


def _write_seed(root: Path) -> None:
    seed_root = root / SEED_ROOT
    seed_root.mkdir(parents=True, exist_ok=True)
    for name, payload in _seed_payloads().items():
        _write_json(seed_root / name, payload)
    checksums = {name: _sha256(seed_root / name) for name in SEED_FILES if name != "seed_manifest.json"}
    _write_json(seed_root / "seed_manifest.json", {"seed_file_checksums": checksums})


@pytest.fixture
def mock_reports(tmp_path: Path) -> Path:
    (tmp_path / "reports/research").mkdir(parents=True)
    (tmp_path / "reports/current").mkdir(parents=True)
    (tmp_path / "docs").mkdir(parents=True)
    _write_seed(tmp_path)

    base_payload = {
        "version": VERSION,
        "version_suffix": VERSION_SUFFIX,
        "corrective_for_version": "V1.93.4",
        "previous_validated_version": "V1.92.1",
        "reviewed_seed_version": "V1.92.1",
        "final_verdict": "V1_93_5_REAL_POST_SEED_VALIDATION_RESTORED",
        "post_seed_review_executed": True,
        "review_only": True,
        "reports_only": True,
        "dataset_seed_created": False,
        "new_dataset_seed_created": False,
        "data_contract_actual_write_executed": False,
        "scope_drift_detected": False,
        "data_directory_writes_allowed": False,
        "data_directory_write_attempted": False,
        "new_data_files_created": False,
        "existing_seed_files_modified": False,
        "no_new_data_directory_writes": True,
        "reviewed_seed_root": str(SEED_ROOT) + "/",
        "reviewed_files_count": 5,
        "expected_files_count": 5,
        "unexpected_files_count": 0,
        "missing_expected_files_count": 0,
        "total_data_bytes_observed": sum((tmp_path / SEED_ROOT / name).stat().st_size for name in SEED_FILES),
        "preview_records_count": 1,
        "seed_manifest_json_valid": True,
        "seed_schema_json_valid": True,
        "seed_preview_records_json_valid": True,
        "seed_provenance_json_valid": True,
        "seed_quality_audit_json_valid": True,
        "manifest_matches_physical_files": True,
        "seed_checksums_verified": True,
        "schema_validation_passed": True,
        "provenance_validation_passed": True,
        "quality_audit_validation_passed": True,
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
        "feature_available_ts_lte_decision_ts_rule_present": True,
        "no_lookahead_policy_present": True,
        "leakage_detected": False,
        "lookahead_detected": False,
        "network_executed": False,
        "new_network_requests_executed": False,
        "trading_allowed": False,
        "real_orders_possible": False,
        "no_strategy_validated": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "ml_signal_validation_executed": False,
        "release_ready_for_external_review": True,
        "clean_zip_ready_for_external_review": True,
        "smoke_test_passed": True,
        "blocking_reason": None,
        "pytest_executed": True,
        "pytest_exit_code": 0,
        "no_pass_only_tests": True,
        "no_pass_anywhere_in_tests": True,
        "no_assert_true_tests": True,
        "no_tautological_assertions": True,
        "no_or_true_tests": True,
        "run_script_generates_test_stub": False,
        "run_script_contains_assert_true_stub": False,
        "bounded_smoke_for_v1_93_5": True,
        "smoke_timeout_detected": False,
        "dataset_created": False,
        "research_dataset_updated": False,
        "labels_created": False,
        "targets_created": False,
        "predictions_created": False,
        "smoke_runs_full_pytest_suite": False,
        "smoke_calls_smoke_script": False,
        "smoke_runs_audit_clean_zip_full_scan": False,
        "release_strict_checks_passed": True,
        "zip_audit_strict_checks_passed": True,
        "zip_smoke_strict_checks_passed": True,
    }

    def write_report(relative: str, payload: dict) -> None:
        path = tmp_path / relative
        _write_json(path, payload)
        path.with_suffix(".md").write_text("# Rapport", encoding="utf-8")

    for suffix in ["summary", "file_audit", "semantic_audit", "safety_check", "consistency_check"]:
        write_report(f"reports/research/mini_research_dataset_post_review_{suffix}_{VERSION_SUFFIX}.json", base_payload)
    write_report("reports/current/latest_metrics.json", base_payload)
    write_report("reports/PROJECT_STATE.json", base_payload)
    (tmp_path / "reports/REPORT_INDEX.md").write_text("V1.93.5 v1_93_5", encoding="utf-8")
    (tmp_path / "docs/code_review_v1_93_5.md").write_text("Review", encoding="utf-8")
    (tmp_path / "docs/mini_research_dataset_post_review_v1_93_5.md").write_text("Doc", encoding="utf-8")

    write_report("reports/release_zip_v1_93_5.json", {
        "version": VERSION,
        "release_zip_created": True,
        "final_zip_created": True,
        "release_ready_for_external_review": True,
        "clean_zip_ready_for_external_review": True,
        "final_audit_passed": True,
        "final_smoke_passed": True,
        "blocking_reason": None,
    })
    write_report("reports/zip_audit_v1_93_5.json", {
        "version": VERSION,
        "clean_zip_ready_for_external_review": True,
        "audit_zip_project_state_version": VERSION,
        "audit_zip_version_parse_correct": True,
        "global_json_finiteness_passed": True,
        "missing_required_files": [],
        "forbidden_count": 0,
    })
    write_report("reports/zip_smoke_test_v1_93_5.json", {
        "version": VERSION,
        "smoke_test_passed": True,
        "smoke_failed_count": 0,
        "smoke_passed_count": 3,
        "smoke_commands_count": 3,
        "smoke_commands_not_empty": True,
        "smoke_timeout_detected": False,
        "bounded_smoke_for_v1_93_5": True,
        "real_orders_possible": False,
        "codex_cli_called": False,
        "holdout_executed": False,
    })
    return tmp_path


def _mutate_json(root: Path, relative: str, **updates: object) -> None:
    path = root / relative
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.update(updates)
    _write_json(path, payload)


def _summary_path(root: Path) -> str:
    return "reports/research/mini_research_dataset_post_review_summary_v1_93_5.json"


def _set_across_state(root: Path, field: str, value: object) -> None:
    for relative in [_summary_path(root), "reports/current/latest_metrics.json", "reports/PROJECT_STATE.json"]:
        _mutate_json(root, relative, **{field: value})


def test_validator_accepts_valid_v1_93_5(mock_reports: Path) -> None:
    assert validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX) == []


def test_validator_rejects_missing_release_zip(mock_reports: Path) -> None:
    (mock_reports / "reports/release_zip_v1_93_5.json").unlink()
    errors = validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX)
    assert any("missing reports/release_zip_v1_93_5.json" in error for error in errors)


def test_validator_rejects_release_final_smoke_false(mock_reports: Path) -> None:
    _mutate_json(mock_reports, "reports/release_zip_v1_93_5.json", final_smoke_passed=False)
    errors = validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX)
    assert any("release: final_smoke_passed" in error for error in errors)


def test_validator_rejects_release_final_audit_false(mock_reports: Path) -> None:
    _mutate_json(mock_reports, "reports/release_zip_v1_93_5.json", final_audit_passed=False)
    errors = validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX)
    assert any("release: final_audit_passed" in error for error in errors)


def test_validator_rejects_release_clean_zip_ready_false(mock_reports: Path) -> None:
    _mutate_json(mock_reports, "reports/release_zip_v1_93_5.json", clean_zip_ready_for_external_review=False)
    errors = validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX)
    assert any("release: clean_zip_ready_for_external_review" in error for error in errors)


def test_validator_rejects_release_blocking_reason_non_null(mock_reports: Path) -> None:
    _mutate_json(mock_reports, "reports/release_zip_v1_93_5.json", blocking_reason="failed")
    errors = validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX)
    assert any("release: blocking_reason" in error for error in errors)


def test_validator_rejects_missing_zip_audit(mock_reports: Path) -> None:
    (mock_reports / "reports/zip_audit_v1_93_5.json").unlink()
    errors = validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX)
    assert any("missing reports/zip_audit_v1_93_5.json" in error for error in errors)


def test_validator_rejects_zip_audit_project_state_version_mismatch(mock_reports: Path) -> None:
    _mutate_json(mock_reports, "reports/zip_audit_v1_93_5.json", audit_zip_project_state_version="V1.92.1")
    errors = validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX)
    assert any("audit: audit_zip_project_state_version" in error for error in errors)


def test_validator_rejects_zip_audit_version_parse_false(mock_reports: Path) -> None:
    _mutate_json(mock_reports, "reports/zip_audit_v1_93_5.json", audit_zip_version_parse_correct=False)
    errors = validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX)
    assert any("audit: audit_zip_version_parse_correct" in error for error in errors)


def test_validator_rejects_zip_audit_global_json_finiteness_false(mock_reports: Path) -> None:
    _mutate_json(mock_reports, "reports/zip_audit_v1_93_5.json", global_json_finiteness_passed=False)
    errors = validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX)
    assert any("audit: global_json_finiteness_passed" in error for error in errors)


def test_validator_rejects_zip_audit_missing_required_files_non_empty(mock_reports: Path) -> None:
    _mutate_json(mock_reports, "reports/zip_audit_v1_93_5.json", missing_required_files=["x"])
    errors = validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX)
    assert any("audit: missing_required_files" in error for error in errors)


def test_validator_rejects_zip_audit_forbidden_count_positive(mock_reports: Path) -> None:
    _mutate_json(mock_reports, "reports/zip_audit_v1_93_5.json", forbidden_count=1)
    errors = validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX)
    assert any("audit: forbidden_count" in error for error in errors)


def test_validator_rejects_missing_zip_smoke(mock_reports: Path) -> None:
    (mock_reports / "reports/zip_smoke_test_v1_93_5.json").unlink()
    errors = validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX)
    assert any("missing reports/zip_smoke_test_v1_93_5.json" in error for error in errors)


def test_validator_rejects_zip_smoke_failed_count_positive(mock_reports: Path) -> None:
    _mutate_json(mock_reports, "reports/zip_smoke_test_v1_93_5.json", smoke_failed_count=1)
    errors = validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX)
    assert any("smoke: smoke_failed_count" in error for error in errors)


def test_validator_rejects_zip_smoke_timeout_true(mock_reports: Path) -> None:
    _mutate_json(mock_reports, "reports/zip_smoke_test_v1_93_5.json", smoke_timeout_detected=True)
    errors = validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX)
    assert any("smoke: smoke_timeout_detected" in error for error in errors)


def test_validator_rejects_zip_smoke_passed_count_mismatch(mock_reports: Path) -> None:
    _mutate_json(mock_reports, "reports/zip_smoke_test_v1_93_5.json", smoke_passed_count=2)
    errors = validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX)
    assert any("smoke: smoke_passed_count != smoke_commands_count" in error for error in errors)


def test_validator_rejects_zip_smoke_test_passed_false(mock_reports: Path) -> None:
    _mutate_json(mock_reports, "reports/zip_smoke_test_v1_93_5.json", smoke_test_passed=False)
    errors = validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX)
    assert any("smoke: smoke_test_passed" in error for error in errors)


def test_validator_rejects_zip_smoke_real_orders_possible_true(mock_reports: Path) -> None:
    _mutate_json(mock_reports, "reports/zip_smoke_test_v1_93_5.json", real_orders_possible=True)
    errors = validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX)
    assert any("smoke: real_orders_possible" in error for error in errors)


def test_validator_rejects_latest_metrics_network_executed_true(mock_reports: Path) -> None:
    _mutate_json(mock_reports, "reports/current/latest_metrics.json", network_executed=True)
    errors = validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX)
    assert any("latest: network_executed diverges from summary" in error for error in errors)


def test_validator_rejects_project_state_dataset_created_true(mock_reports: Path) -> None:
    _mutate_json(mock_reports, "reports/PROJECT_STATE.json", dataset_created=True)
    errors = validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX)
    assert any("project: dataset_created diverges from summary" in error for error in errors)


def test_validator_rejects_summary_dataset_created_true(mock_reports: Path) -> None:
    _set_across_state(mock_reports, "dataset_created", True)
    errors = validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX)
    assert any("dataset_created != false" in error for error in errors)


def test_validator_rejects_cross_file_version_mismatch(mock_reports: Path) -> None:
    _mutate_json(mock_reports, "reports/current/latest_metrics.json", version="V1.93.4")
    errors = validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX)
    assert any("latest: version diverges from summary" in error for error in errors)


def test_validator_rejects_missing_critical_field_in_latest_metrics(mock_reports: Path) -> None:
    path = mock_reports / "reports/current/latest_metrics.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.pop("network_executed")
    _write_json(path, payload)
    errors = validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX)
    assert any("latest: missing critical field network_executed" in error for error in errors)


def test_validator_rejects_missing_critical_field_in_project_state(mock_reports: Path) -> None:
    path = mock_reports / "reports/PROJECT_STATE.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.pop("dataset_created")
    _write_json(path, payload)
    errors = validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX)
    assert any("project: missing critical field dataset_created" in error for error in errors)


@pytest.mark.parametrize("filename", SEED_FILES)
def test_validator_rejects_missing_seed_files(mock_reports: Path, filename: str) -> None:
    (mock_reports / SEED_ROOT / filename).unlink()
    errors = validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX)
    assert any(f"missing seed file {filename}" in error or "seed files mismatch" in error for error in errors)


def test_validator_rejects_extra_file_in_seed_root(mock_reports: Path) -> None:
    _write_json(mock_reports / SEED_ROOT / "extra.json", {"extra": True})
    errors = validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX)
    assert any("unexpected seed file extra.json" in error for error in errors)


def test_validator_rejects_invalid_json_seed_file(mock_reports: Path) -> None:
    (mock_reports / SEED_ROOT / "seed_schema.json").write_text("{bad", encoding="utf-8")
    errors = validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX)
    assert any("file seed_schema.json is not valid JSON" in error for error in errors)


def test_validator_rejects_seed_checksum_mismatch(mock_reports: Path) -> None:
    _write_json(mock_reports / SEED_ROOT / "seed_schema.json", {"fields": [{"name": "available_ts"}]})
    errors = validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX)
    assert any("physical seed checksums not verified" in error for error in errors)


def test_validator_rejects_preview_records_above_10(mock_reports: Path) -> None:
    records = [{"available_ts": str(i), "decision_ts": str(i)} for i in range(11)]
    _write_json(mock_reports / SEED_ROOT / "seed_preview_records.json", {"records": records})
    errors = validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX)
    assert any("physical seed preview_records_count > 10" in error for error in errors)


def _recompute_manifest(root: Path) -> None:
    seed_root = root / SEED_ROOT
    checksums = {name: _sha256(seed_root / name) for name in SEED_FILES if name != "seed_manifest.json"}
    _write_json(seed_root / "seed_manifest.json", {"seed_file_checksums": checksums})


def test_review_rejects_target_return_in_schema_even_with_recomputed_checksum(mock_reports: Path) -> None:
    _write_json(mock_reports / SEED_ROOT / "seed_schema.json", {"fields": [{"name": "target_return"}]})
    _recompute_manifest(mock_reports)
    errors = validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX)
    assert any("forbidden terms detected in seed" in error for error in errors)


def test_review_rejects_future_return_in_preview_records_even_with_recomputed_checksum(mock_reports: Path) -> None:
    _write_json(mock_reports / SEED_ROOT / "seed_preview_records.json", {"records": [{"future_return_1h": 0.1}]})
    _recompute_manifest(mock_reports)
    errors = validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX)
    assert any("forbidden terms detected in seed" in error for error in errors)


@pytest.mark.parametrize("filename,key", [
    ("seed_manifest.json", "prediction_score"),
    ("seed_provenance.json", "label_up_down"),
    ("seed_quality_audit.json", "expected_value"),
    ("seed_quality_audit.json", "mfe"),
    ("seed_quality_audit.json", "mae"),
    ("seed_quality_audit.json", "pnl"),
    ("seed_quality_audit.json", "profit"),
])
def test_review_rejects_forbidden_terms_anywhere(mock_reports: Path, filename: str, key: str) -> None:
    _write_json(mock_reports / SEED_ROOT / filename, {key: "bad"})
    if filename != "seed_manifest.json":
        _recompute_manifest(mock_reports)
    errors = validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX)
    assert any("forbidden terms detected in seed" in error for error in errors)


def test_semantic_scan_reports_file_and_json_path(mock_reports: Path) -> None:
    _write_json(mock_reports / SEED_ROOT / "seed_schema.json", {"nested": {"target_return": "bad"}})
    _recompute_manifest(mock_reports)
    errors = validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX)
    message = "\n".join(errors)
    assert "seed_schema.json" in message and "json_path" in message


def test_smoke_v1_93_5_fast_path_exists() -> None:
    content = (PROJECT_ROOT / "scripts/smoke_test_clean_zip.py").read_text(encoding="utf-8")
    assert "_fast_smoke_v1_93_5" in content


def test_smoke_v1_93_5_uses_only_three_commands(mock_reports: Path) -> None:
    payload = json.loads((mock_reports / "reports/zip_smoke_test_v1_93_5.json").read_text(encoding="utf-8"))
    assert payload["smoke_commands_count"] == 3


def test_report_index_references_v1_93_5(mock_reports: Path) -> None:
    (mock_reports / "reports/REPORT_INDEX.md").write_text("V1.93.4", encoding="utf-8")
    errors = validate_report_set(mock_reports, version_suffix=VERSION_SUFFIX)
    assert any("REPORT_INDEX does not reference V1.93.5" in error for error in errors)


def test_no_pass_anywhere_in_v1_93_5_tests() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    pass_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.Pass)]
    assert pass_nodes == []


def test_no_assert_true_or_true_in_v1_93_5() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assert) and isinstance(node.test, ast.Constant) and node.test.value is True:
            findings.append("literal_true")
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
            findings.extend("or_true" for value in node.values if isinstance(value, ast.Constant) and value.value is True)
    assert findings == []


def _constant_value(node: ast.AST) -> object:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp):
        left = _constant_value(node.left)
        right = _constant_value(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
    return None


def test_no_tautological_assertions_in_v1_93_5() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    tautologies = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assert) and isinstance(node.test, ast.Compare):
            if len(node.test.ops) == 1 and len(node.test.comparators) == 1:
                left = _constant_value(node.test.left)
                right = _constant_value(node.test.comparators[0])
                if left is not None and right is not None and isinstance(node.test.ops[0], ast.Eq) and left == right:
                    tautologies.append((left, right))
    assert tautologies == []
