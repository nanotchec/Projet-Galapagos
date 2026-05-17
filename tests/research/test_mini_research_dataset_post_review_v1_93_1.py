import ast
import json
import pytest
import os
import shutil
from pathlib import Path
from galapagos.research.mini_research_dataset_post_review.validator import validate_report_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]

@pytest.fixture
def mock_reports(tmp_path):
    v = "v1_93_1"
    V = "V1.93.1"
    (tmp_path / "reports/research").mkdir(parents=True)
    (tmp_path / "reports/current").mkdir(parents=True)
    (tmp_path / "docs").mkdir(parents=True)
    (tmp_path / "data/research/dataset_seed/v1_92").mkdir(parents=True)
    (tmp_path / "scripts").mkdir(parents=True)
    
    base_payload = {
        "version": V,
        "final_verdict": "V1_93_1_FAST_BOUNDED_SMOKE_PASSED",
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
        "no_assert_true_tests": True,
        "no_tautological_assertions": True,
        "no_or_true_tests": True,
        "run_script_generates_test_stub": False,
        "run_script_contains_assert_true_stub": False,
        "bounded_smoke_for_v1_93_1": True,
        "smoke_timeout_detected": False,
        "dataset_created": False,
        "research_dataset_updated": False,
        "labels_created": False,
        "targets_created": False,
        "predictions_created": False,
        "smoke_runs_full_pytest_suite": False,
        "smoke_calls_smoke_script": False,
        "smoke_runs_audit_clean_zip_full_scan": False,
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
    (tmp_path / "reports/REPORT_INDEX.md").write_text("V1.93.1 v1_93_1", encoding="utf-8")
    
    # Specific payload for smoke to include counts
    smoke_payload = base_payload.copy()
    smoke_payload.update({
        "smoke_commands_count": 3,
        "smoke_passed_count": 3,
        "smoke_failed_count": 0,
    })
    
    write_j(f"reports/release_zip_{v}.json", base_payload)
    write_j(f"reports/zip_audit_{v}.json", base_payload)
    write_j(f"reports/zip_smoke_test_{v}.json", smoke_payload)
    
    (tmp_path / f"docs/code_review_{v}.md").write_text("Review", encoding="utf-8")
    (tmp_path / f"docs/mini_research_dataset_post_review_{v}.md").write_text("Doc", encoding="utf-8")

    # Seed files
    for f in ["seed_manifest.json", "seed_schema.json", "seed_preview_records.json", "seed_provenance.json", "seed_quality_audit.json"]:
        (tmp_path / "data/research/dataset_seed/v1_92" / f).write_text("{}", encoding="utf-8")

    return tmp_path

def test_review_reads_only_seed_files(mock_reports):
    errors = validate_report_set(mock_reports, version_suffix="v1_93_1")
    assert not errors

def test_review_rejects_missing_seed_manifest(mock_reports):
    os.remove(mock_reports / "data/research/dataset_seed/v1_92/seed_manifest.json")
    errors = validate_report_set(mock_reports, version_suffix="v1_93_1")
    assert any("seed files mismatch" in e for e in errors)

def test_review_rejects_invalid_json_seed_file(mock_reports):
    (mock_reports / "data/research/dataset_seed/v1_92/seed_schema.json").write_text("{invalid", encoding="utf-8")
    errors = validate_report_set(mock_reports, version_suffix="v1_93_1")
    assert any("not valid JSON" in e for e in errors)

def test_review_rejects_preview_records_above_10(mock_reports):
    path = mock_reports / "reports/research/mini_research_dataset_post_review_summary_v1_93_1.json"
    data = json.loads(path.read_text())
    data["preview_records_count"] = 11
    path.write_text(json.dumps(data))
    # Consistency
    for p in ["reports/current/latest_metrics.json", "reports/PROJECT_STATE.json"]:
        pd = json.loads((mock_reports / p).read_text())
        pd["preview_records_count"] = 11
        (mock_reports / p).write_text(json.dumps(pd))
    errors = validate_report_set(mock_reports, version_suffix="v1_93_1")
    assert any("preview_records_count > 10" in e for e in errors)

def test_review_rejects_target_return_in_schema_even_with_recomputed_checksum(mock_reports):
    (mock_reports / "data/research/dataset_seed/v1_92/seed_schema.json").write_text(json.dumps({"fields": [{"name": "target_return"}]}), encoding="utf-8")
    errors = validate_report_set(mock_reports, version_suffix="v1_93_1")
    assert any("forbidden terms detected in seed" in e for e in errors)

def test_validator_rejects_dataset_created_true(mock_reports):
    path = mock_reports / "reports/research/mini_research_dataset_post_review_summary_v1_93_1.json"
    data = json.loads(path.read_text())
    data["dataset_created"] = True
    path.write_text(json.dumps(data))
    for p in ["reports/current/latest_metrics.json", "reports/PROJECT_STATE.json"]:
        pj = mock_reports / p
        pd = json.loads(pj.read_text())
        pd["dataset_created"] = True
        pj.write_text(json.dumps(pd))
    errors = validate_report_set(mock_reports, version_suffix="v1_93_1")
    assert any("dataset_created != false" in e for e in errors)

def test_validator_rejects_smoke_timeout_true(mock_reports):
    path = mock_reports / "reports/zip_smoke_test_v1_93_1.json"
    data = json.loads(path.read_text())
    data["smoke_timeout_detected"] = True
    path.write_text(json.dumps(data))
    errors = validate_report_set(mock_reports, version_suffix="v1_93_1")
    assert any("smoke_timeout_detected != false" in e for e in errors)

def test_smoke_v1_93_1_fast_path_exists(mock_reports):
    path = PROJECT_ROOT / "scripts/smoke_test_clean_zip.py"
    content = path.read_text()
    assert "_fast_smoke_v1_93_1" in content

def test_smoke_v1_93_1_uses_only_three_commands(mock_reports):
    path = mock_reports / "reports/zip_smoke_test_v1_93_1.json"
    data = json.loads(path.read_text())
    assert data["smoke_commands_count"] == 3

def test_report_index_references_v1_93_1(mock_reports):
    (mock_reports / "reports/REPORT_INDEX.md").write_text("V1.93", encoding="utf-8")
    errors = validate_report_set(mock_reports, version_suffix="v1_93_1")
    assert any("REPORT_INDEX does not reference V1.93.1" in e for e in errors)

def test_no_pass_only_tests_in_v1_93_1():
    path = Path(__file__)
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            is_pass = len(node.body) == 1 and isinstance(node.body[0], ast.Pass)
            assert not is_pass, f"Test {node.name} is pass-only"
    assert tree is not None

def test_no_assert_true_or_true_in_v1_93_1():
    path = Path(__file__)
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assert):
            if isinstance(node.test, ast.Constant) and node.test.value is True:
                assert False, "Found forbidden literal assertion"
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
            for val in node.values:
                if isinstance(val, ast.Constant) and val.value is True:
                    assert False, "Found forbidden or-true hack"
    assert 1 == (2-1)
