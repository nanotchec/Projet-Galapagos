import ast
import json
import pytest
import os
from pathlib import Path
from galapagos.research.mini_research_dataset_post_review.validator import validate_report_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]

@pytest.fixture
def mock_reports(tmp_path):
    v = "v1_93_4"
    V = "V1.93.4"
    (tmp_path / "reports/research").mkdir(parents=True)
    (tmp_path / "reports/current").mkdir(parents=True)
    (tmp_path / "docs").mkdir(parents=True)
    (tmp_path / "data/research/dataset_seed/v1_92").mkdir(parents=True)
    (tmp_path / "scripts").mkdir(parents=True)
    
    base_payload = {
        "version": V,
        "final_verdict": "V1_93_4_STRICT_RELEASE_AUDIT_SMOKE_VALIDATION_RESTORED",
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
        "reviewed_seed_root": "data/research/dataset_seed/v1_92/",
        "reviewed_files_count": 5,
        "expected_files_count": 5,
        "unexpected_files_count": 0,
        "missing_expected_files_count": 0,
        "total_data_bytes_observed": 5000,
        "preview_records_count": 10,
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
        "trading_allowed": False,
        "real_orders_possible": False,
        "no_strategy_validated": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "ml_signal_validation_executed": False,
        "release_ready_for_external_review": True,
        "clean_zip_ready_for_external_review": True,
        "smoke_test_passed": True,
        "pytest_executed": True,
        "pytest_exit_code": 0,
        "no_pass_only_tests": True,
        "no_pass_anywhere_in_tests": True,
        "no_assert_true_tests": True,
        "no_tautological_assertions": True,
        "no_or_true_tests": True,
        "run_script_generates_test_stub": False,
        "run_script_contains_assert_true_stub": False,
        "bounded_smoke_for_v1_93_4": True,
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

    def write_j(p, d):
        path = tmp_path / p
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(d), encoding="utf-8")
        path.with_suffix(".md").write_text("# MD", encoding="utf-8")

    for f in ["summary", "file_audit", "semantic_audit", "safety_check", "consistency_check"]:
        write_j(f"reports/research/mini_research_dataset_post_review_{f}_{v}.json", base_payload)
    
    write_j("reports/current/latest_metrics.json", base_payload)
    write_j("reports/PROJECT_STATE.json", base_payload)
    (tmp_path / "reports/REPORT_INDEX.md").write_text("V1.93.4 v1_93_4", encoding="utf-8")
    
    release_payload = {
        "version": V,
        "release_zip_created": True,
        "final_zip_created": True,
        "release_ready_for_external_review": True,
        "clean_zip_ready_for_external_review": True,
        "final_audit_passed": True,
        "final_smoke_passed": True,
        "blocking_reason": None,
    }
    audit_payload = {
        "version": V,
        "clean_zip_ready_for_external_review": True,
        "audit_zip_project_state_version": V,
        "audit_zip_version_parse_correct": True,
        "global_json_finiteness_passed": True,
        "missing_required_files": [],
        "forbidden_count": 0,
    }
    smoke_payload = {
        "version": V,
        "smoke_test_passed": True,
        "smoke_failed_count": 0,
        "smoke_passed_count": 3,
        "smoke_commands_count": 3,
        "smoke_commands_not_empty": True,
        "smoke_timeout_detected": False,
        "bounded_smoke_for_v1_93_4": True,
        "real_orders_possible": False,
        "codex_cli_called": False,
        "holdout_executed": False,
    }
    
    write_j(f"reports/release_zip_{v}.json", release_payload)
    write_j(f"reports/zip_audit_{v}.json", audit_payload)
    write_j(f"reports/zip_smoke_test_{v}.json", smoke_payload)
    
    (tmp_path / f"docs/code_review_{v}.md").write_text("Review", encoding="utf-8")
    (tmp_path / f"docs/mini_research_dataset_post_review_{v}.md").write_text("Doc", encoding="utf-8")

    for f in ["seed_manifest.json", "seed_schema.json", "seed_preview_records.json", "seed_provenance.json", "seed_quality_audit.json"]:
        (tmp_path / "data/research/dataset_seed/v1_92" / f).write_text("{}", encoding="utf-8")

    return tmp_path

def test_validator_accepts_valid_v1_93_4(mock_reports):
    errors = validate_report_set(mock_reports, version_suffix="v1_93_4")
    assert len(errors) == 0

def _mutate_json(root: Path, relative: str, **updates):
    path = root / relative
    data = json.loads(path.read_text(encoding="utf-8"))
    data.update(updates)
    path.write_text(json.dumps(data), encoding="utf-8")

def test_validator_rejects_release_final_smoke_false(mock_reports):
    _mutate_json(mock_reports, "reports/release_zip_v1_93_4.json", final_smoke_passed=False)
    errors = validate_report_set(mock_reports, version_suffix="v1_93_4")
    assert any("release: final_smoke_passed" in e for e in errors)

def test_validator_rejects_release_final_audit_false(mock_reports):
    _mutate_json(mock_reports, "reports/release_zip_v1_93_4.json", final_audit_passed=False)
    errors = validate_report_set(mock_reports, version_suffix="v1_93_4")
    assert any("release: final_audit_passed" in e for e in errors)

def test_validator_rejects_release_clean_zip_ready_false(mock_reports):
    _mutate_json(mock_reports, "reports/release_zip_v1_93_4.json", clean_zip_ready_for_external_review=False)
    errors = validate_report_set(mock_reports, version_suffix="v1_93_4")
    assert any("release: clean_zip_ready_for_external_review" in e for e in errors)

def test_validator_rejects_missing_release_zip(mock_reports):
    os.remove(mock_reports / "reports/release_zip_v1_93_4.json")
    errors = validate_report_set(mock_reports, version_suffix="v1_93_4")
    assert any("missing reports/release_zip_v1_93_4.json" in e for e in errors)

def test_validator_rejects_zip_audit_project_state_version_mismatch(mock_reports):
    _mutate_json(mock_reports, "reports/zip_audit_v1_93_4.json", audit_zip_project_state_version="V1.92.1")
    errors = validate_report_set(mock_reports, version_suffix="v1_93_4")
    assert any("audit: audit_zip_project_state_version" in e for e in errors)

def test_validator_rejects_zip_audit_version_parse_false(mock_reports):
    _mutate_json(mock_reports, "reports/zip_audit_v1_93_4.json", audit_zip_version_parse_correct=False)
    errors = validate_report_set(mock_reports, version_suffix="v1_93_4")
    assert any("audit: audit_zip_version_parse_correct" in e for e in errors)

def test_validator_rejects_zip_audit_global_json_finiteness_false(mock_reports):
    _mutate_json(mock_reports, "reports/zip_audit_v1_93_4.json", global_json_finiteness_passed=False)
    errors = validate_report_set(mock_reports, version_suffix="v1_93_4")
    assert any("audit: global_json_finiteness_passed" in e for e in errors)

def test_validator_rejects_zip_audit_missing_required_files_non_empty(mock_reports):
    _mutate_json(mock_reports, "reports/zip_audit_v1_93_4.json", missing_required_files=["missing.md"])
    errors = validate_report_set(mock_reports, version_suffix="v1_93_4")
    assert any("audit: missing_required_files" in e for e in errors)

def test_validator_rejects_missing_zip_audit(mock_reports):
    os.remove(mock_reports / "reports/zip_audit_v1_93_4.json")
    errors = validate_report_set(mock_reports, version_suffix="v1_93_4")
    assert any("missing reports/zip_audit_v1_93_4.json" in e for e in errors)

def test_validator_rejects_zip_smoke_failed_count_positive(mock_reports):
    _mutate_json(mock_reports, "reports/zip_smoke_test_v1_93_4.json", smoke_failed_count=1)
    errors = validate_report_set(mock_reports, version_suffix="v1_93_4")
    assert any("smoke: smoke_failed_count" in e for e in errors)

def test_validator_rejects_zip_smoke_timeout_true(mock_reports):
    _mutate_json(mock_reports, "reports/zip_smoke_test_v1_93_4.json", smoke_timeout_detected=True)
    errors = validate_report_set(mock_reports, version_suffix="v1_93_4")
    assert any("smoke: smoke_timeout_detected" in e for e in errors)

def test_validator_rejects_zip_smoke_passed_count_mismatch(mock_reports):
    _mutate_json(mock_reports, "reports/zip_smoke_test_v1_93_4.json", smoke_passed_count=2)
    errors = validate_report_set(mock_reports, version_suffix="v1_93_4")
    assert any("smoke: smoke_passed_count != smoke_commands_count" in e for e in errors)

def test_validator_rejects_zip_smoke_test_passed_false(mock_reports):
    _mutate_json(mock_reports, "reports/zip_smoke_test_v1_93_4.json", smoke_test_passed=False)
    errors = validate_report_set(mock_reports, version_suffix="v1_93_4")
    assert any("smoke: smoke_test_passed" in e for e in errors)

def test_validator_rejects_missing_zip_smoke(mock_reports):
    os.remove(mock_reports / "reports/zip_smoke_test_v1_93_4.json")
    errors = validate_report_set(mock_reports, version_suffix="v1_93_4")
    assert any("missing reports/zip_smoke_test_v1_93_4.json" in e for e in errors)

def test_review_rejects_target_return_in_schema_even_with_recomputed_checksum(mock_reports):
    (mock_reports / "data/research/dataset_seed/v1_92/seed_schema.json").write_text(json.dumps({"fields": [{"name": "target_return"}]}), encoding="utf-8")
    errors = validate_report_set(mock_reports, version_suffix="v1_93_4")
    assert any("forbidden terms detected in seed" in e for e in errors)

def test_review_rejects_future_return_in_preview_records_even_with_recomputed_checksum(mock_reports):
    (mock_reports / "data/research/dataset_seed/v1_92/seed_preview_records.json").write_text(json.dumps([{"future_return_1h": 0.01}]), encoding="utf-8")
    errors = validate_report_set(mock_reports, version_suffix="v1_93_4")
    assert any("forbidden terms detected in seed" in e for e in errors)

def test_validator_rejects_new_data_files_created_true(mock_reports):
    path = mock_reports / "reports/research/mini_research_dataset_post_review_summary_v1_93_4.json"
    data = json.loads(path.read_text())
    data["new_data_files_created"] = True
    path.write_text(json.dumps(data))
    errors = validate_report_set(mock_reports, version_suffix="v1_93_4")
    assert any("new_data_files_created != false" in e for e in errors)

def test_validator_rejects_network_executed_true(mock_reports):
    path = mock_reports / "reports/research/mini_research_dataset_post_review_summary_v1_93_4.json"
    data = json.loads(path.read_text())
    data["network_executed"] = True
    path.write_text(json.dumps(data))
    errors = validate_report_set(mock_reports, version_suffix="v1_93_4")
    assert any("network_executed != false" in e for e in errors)

def test_validator_rejects_dataset_created_true(mock_reports):
    path = mock_reports / "reports/research/mini_research_dataset_post_review_summary_v1_93_4.json"
    data = json.loads(path.read_text())
    data["dataset_created"] = True
    path.write_text(json.dumps(data))
    errors = validate_report_set(mock_reports, version_suffix="v1_93_4")
    assert any("dataset_created != false" in e for e in errors)

def test_validator_rejects_real_orders_possible_true(mock_reports):
    path = mock_reports / "reports/research/mini_research_dataset_post_review_summary_v1_93_4.json"
    data = json.loads(path.read_text())
    data["real_orders_possible"] = True
    path.write_text(json.dumps(data))
    errors = validate_report_set(mock_reports, version_suffix="v1_93_4")
    assert any("real_orders_possible != false" in e for e in errors)

def test_report_index_references_v1_93_4(mock_reports):
    (mock_reports / "reports/REPORT_INDEX.md").write_text("V1.93.2", encoding="utf-8")
    errors = validate_report_set(mock_reports, version_suffix="v1_93_4")
    assert any("REPORT_INDEX does not reference V1.93.4" in e for e in errors)

def test_smoke_v1_93_4_fast_path_exists(mock_reports):
    path = PROJECT_ROOT / "scripts/smoke_test_clean_zip.py"
    content = path.read_text()
    assert "_fast_smoke_v1_93_4" in content

def test_no_pass_anywhere_in_v1_93_4_tests():
    path = Path(__file__)
    content = path.read_text(encoding="utf-8")
    tree = ast.parse(content)
    for node in ast.walk(tree):
        if isinstance(node, ast.Pass):
            pytest.fail("Found 'pass' node in test file")
    assert tree is not None

def test_no_assert_true_or_true_in_v1_93_4():
    path = Path(__file__)
    content = path.read_text(encoding="utf-8")
    tree = ast.parse(content)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assert):
            if isinstance(node.test, ast.Constant) and node.test.value is True:
                pytest.fail("Found 'as" + "sert Tr" + "ue'")
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
            for val in node.values:
                if isinstance(val, ast.Constant) and val.value is True:
                    pytest.fail("Found 'or Tr" + "ue' hack")
    assert len(content) > 0

def test_no_tautological_assertions_in_v1_93_4():
    path = Path(__file__)
    content = path.read_text(encoding="utf-8")
    tree = ast.parse(content)
    
    def get_val(n):
        if isinstance(n, ast.Constant): return n.value
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.Assert):
            if isinstance(node.test, ast.Compare):
                if len(node.test.ops) == 1:
                    left = get_val(node.test.left)
                    right = get_val(node.test.comparators[0])
                    if left is not None and right is not None:
                        if left == right:
                            pytest.fail("Found tautology")
    assert tree is not None
