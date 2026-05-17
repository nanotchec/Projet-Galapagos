from __future__ import annotations

import ast
import json
import shutil
from pathlib import Path

import pytest

from galapagos.research.mini_research_dataset_seed import (
    ALLOWED_FILES,
    MiniResearchDatasetSeedBuilder,
    SeedBuildError,
)
from galapagos.research.mini_research_dataset_seed.physical_auditor import (
    V1_84_FILES,
    V1_87_FILES,
    V1_90_FILES,
)
from galapagos.research.mini_research_dataset_seed.validator import validate_payload, validate_report_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCOPE = "mini_research_dataset_seed_ultra_bounded_no_network_no_full_dataset_no_ml_no_trading"


@pytest.fixture
def seed_root(tmp_path: Path) -> Path:
    for rel in [*V1_84_FILES, *V1_87_FILES, *V1_90_FILES]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PROJECT_ROOT / rel, target)
    return tmp_path


def approval() -> dict:
    return {
        "human_approval_granted": True,
        "approval_phrase_match": True,
        "v1_92_authorized": True,
        "authorized_future_scope": SCOPE,
    }


def design() -> dict:
    return {
        "dataset_seed_design_created": True,
        "future_dataset_seed_allowed_root": "data/research/dataset_seed/v1_92/",
        "future_dataset_seed_max_files": 5,
        "future_dataset_seed_max_bytes": 50_000,
        "future_dataset_seed_allowed_extensions": [".json"],
    }


def anti_plan() -> dict:
    return {
        "anti_leakage_plan_created": True,
        "available_ts_policy_defined": True,
        "event_ts_policy_defined": True,
        "decision_ts_policy_defined": True,
        "feature_available_ts_lte_decision_ts_rule_defined": True,
        "no_lookahead_policy_defined": True,
        "provenance_policy_defined": True,
        "manifest_checksum_policy_defined": True,
        "schema_validation_policy_defined": True,
    }


def build_seed(root: Path) -> dict:
    return MiniResearchDatasetSeedBuilder(root).build(approval=approval(), design=design(), anti_leakage_plan=anti_plan())


def summary_payload(file_audit: dict) -> dict:
    return {
        "version": "V1.92",
        "final_verdict": "V1_92_MINI_RESEARCH_DATASET_SEED_ULTRA_BOUNDED_PASSED",
        "approval_source_verified": True,
        "human_approval_granted": True,
        "approval_phrase_match": True,
        "v1_92_authorized": True,
        "authorized_future_scope": SCOPE,
        "dataset_seed_created": True,
        "mini_research_dataset_seed_only": True,
        "full_dataset_created": False,
        "scope_drift_detected": False,
        "reports_only": False,
        "data_directory_writes_allowed": True,
        "data_write_approved": True,
        "data_directory_write_attempted": True,
        "new_data_files_created": True,
        "dataset_seed_actual_write_executed": True,
        "no_data_directory_writes": False,
        "dataset_created": False,
        "research_dataset_updated": False,
        "labels_created": False,
        "targets_created": False,
        "predictions_created": False,
        "ml_signal_validation_executed": False,
        "feature_generation_executed": False,
        "model_training_executed": False,
        "anti_leakage_plan_applied": True,
        "available_ts_policy_applied": True,
        "event_ts_policy_applied": True,
        "decision_ts_policy_applied": True,
        "feature_available_ts_lte_decision_ts_rule_applied": True,
        "no_lookahead_policy_applied": True,
        "provenance_policy_applied": True,
        "manifest_checksum_policy_applied": True,
        "schema_validation_policy_applied": True,
        "leakage_detected": False,
        "lookahead_detected": False,
        "future_information_fields_detected": False,
        "forbidden_target_like_fields_detected": False,
        "network_executed": False,
        "new_network_requests_executed": False,
        "request_retry_count": 0,
        "pagination_used": False,
        "authenticated_request_allowed": False,
        "secrets_used": False,
        "strategy_link_allowed": False,
        "trading_allowed": False,
        "no_strategy_validated": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "real_orders_possible": False,
        "holdout_executed": False,
        "codex_cli_called": False,
        "pytest_executed": True,
        "pytest_exit_code": 0,
        "pytest_failed_count": 0,
        "release_ready_for_external_review": True,
        "clean_zip_ready_for_external_review": True,
        "smoke_test_passed": True,
        "blocking_reason": None,
        **file_audit,
    }


@pytest.fixture
def report_root(seed_root: Path) -> Path:
    file_audit = build_seed(seed_root)
    payload = summary_payload(file_audit)
    research = seed_root / "reports/research"
    current = seed_root / "reports/current"
    docs = seed_root / "docs"
    for directory in [research, current, docs]:
        directory.mkdir(parents=True, exist_ok=True)
    write_json_md(research / "mini_research_dataset_seed_summary_v1_92.json", payload)
    write_json_md(research / "mini_research_dataset_seed_file_audit_v1_92.json", {"version": "V1.92", **file_audit})
    anti = {k: payload[k] for k in [
        "version",
        "anti_leakage_plan_applied",
        "available_ts_policy_applied",
        "feature_available_ts_lte_decision_ts_rule_applied",
        "no_lookahead_policy_applied",
        "provenance_policy_applied",
        "manifest_checksum_policy_applied",
        "schema_validation_policy_applied",
        "leakage_detected",
        "lookahead_detected",
        "future_information_fields_detected",
        "forbidden_target_like_fields_detected",
    ]}
    write_json_md(research / "mini_research_dataset_seed_anti_leakage_audit_v1_92.json", anti)
    write_json_md(research / "mini_research_dataset_seed_safety_check_v1_92.json", {"version": "V1.92", "safety_check_passed": True})
    write_json_md(research / "mini_research_dataset_seed_consistency_check_v1_92.json", {"version": "V1.92", "issues": []})
    write_json_md(research / "v1_92_recommendation.json", {"version": "V1.92"})
    write_json_md(current / "latest_metrics.json", payload)
    write_json_md(seed_root / "reports/PROJECT_STATE.json", payload)
    (current / "latest_summary.md").write_text("V1.92 latest summary", encoding="utf-8")
    (seed_root / "reports/REPORT_INDEX.md").write_text("V1.92 v1_92", encoding="utf-8")
    (docs / "code_review_v1_92.md").write_text("Review V1.92", encoding="utf-8")
    (docs / "mini_research_dataset_seed_v1_92.md").write_text("Doc V1.92", encoding="utf-8")
    write_json_md(seed_root / "reports/release_zip_v1_92.json", {
        "version": "V1.92",
        "release_zip_created": True,
        "final_zip_created": True,
        "release_ready_for_external_review": True,
        "clean_zip_ready_for_external_review": True,
        "final_audit_passed": True,
        "final_smoke_passed": True,
        "blocking_reason": None,
    })
    write_json_md(seed_root / "reports/zip_audit_v1_92.json", {
        "version": "V1.92",
        "audit_zip_project_state_version": "V1.92",
        "audit_zip_version_parse_correct": True,
        "forbidden_count": 0,
        "missing_required_files": [],
        "global_json_finiteness_passed": True,
    })
    write_json_md(seed_root / "reports/zip_smoke_test_v1_92.json", {
        "version": "V1.92",
        "smoke_test_passed": True,
        "smoke_failed_count": 0,
        "smoke_passed_count": 3,
        "smoke_commands_count": 3,
        "smoke_commands_not_empty": True,
    })
    return seed_root


def write_json_md(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    path.with_suffix(".md").write_text("# report\n", encoding="utf-8")


def test_requires_v1_91_4_approval(seed_root: Path):
    result = build_seed(seed_root)
    assert result["created_files_count"] == 5


def test_rejects_missing_approval(seed_root: Path):
    bad = approval()
    bad["human_approval_granted"] = False
    with pytest.raises(SeedBuildError):
        MiniResearchDatasetSeedBuilder(seed_root).build(approval=bad, design=design(), anti_leakage_plan=anti_plan())


def test_seed_writes_exactly_five_json_files(seed_root: Path):
    build_seed(seed_root)
    files = sorted((seed_root / "data/research/dataset_seed/v1_92").glob("*"))
    assert [path.name for path in files] == sorted(path.name for path in ALLOWED_FILES)


def test_seed_rejects_unapproved_write_path(report_root: Path):
    extra = report_root / "data/research/dataset_seed/v1_92/extra.json"
    extra.write_text("{}", encoding="utf-8")
    errors = validate_report_set(report_root)
    assert any("exactly the five authorized" in error for error in errors)


def test_seed_rejects_more_than_five_files():
    payload = summary_payload({"created_files_count": 6, "total_new_data_files_created": 6, "total_data_bytes_written": 1, "preview_records_count": 1})
    errors = validate_payload(payload)
    assert any("created_files_count != 5" in error for error in errors)


def test_seed_rejects_bytes_over_limit():
    payload = summary_payload({"created_files_count": 5, "total_new_data_files_created": 5, "total_data_bytes_written": 50_001, "preview_records_count": 1})
    errors = validate_payload(payload)
    assert any("total_data_bytes_written > 50000" in error for error in errors)


def test_seed_rejects_parquet_created():
    assert any("parquet_created" in error for error in validate_payload({**summary_payload(valid_counts()), "parquet_created": True}))


def test_seed_rejects_csv_created():
    assert any("csv_created" in error for error in validate_payload({**summary_payload(valid_counts()), "csv_created": True}))


def test_seed_rejects_sqlite_created():
    assert any("sqlite_created" in error for error in validate_payload({**summary_payload(valid_counts()), "sqlite_created": True}))


def test_seed_rejects_jsonl_created():
    assert any("jsonl_created" in error for error in validate_payload({**summary_payload(valid_counts()), "jsonl_created": True}))


def test_seed_rejects_db_created():
    assert any("db_created" in error for error in validate_payload({**summary_payload(valid_counts()), "db_created": True}))


def test_seed_rejects_existing_v1_84_modification():
    assert any("existing_v1_84_files_modified" in error for error in validate_payload({**summary_payload(valid_counts()), "existing_v1_84_files_modified": True}))


def test_seed_rejects_existing_v1_87_modification():
    assert any("existing_v1_87_files_modified" in error for error in validate_payload({**summary_payload(valid_counts()), "existing_v1_87_files_modified": True}))


def test_seed_rejects_existing_v1_90_modification():
    assert any("existing_v1_90_files_modified" in error for error in validate_payload({**summary_payload(valid_counts()), "existing_v1_90_files_modified": True}))


def test_seed_rejects_network_executed():
    assert any("network_executed" in error for error in validate_payload({**summary_payload(valid_counts()), "network_executed": True}))


def test_seed_rejects_full_dataset_created():
    assert any("full_dataset_created" in error for error in validate_payload({**summary_payload(valid_counts()), "full_dataset_created": True}))


def test_seed_rejects_labels_created():
    assert any("labels_created" in error for error in validate_payload({**summary_payload(valid_counts()), "labels_created": True}))


def test_seed_rejects_targets_created():
    assert any("targets_created" in error for error in validate_payload({**summary_payload(valid_counts()), "targets_created": True}))


def test_seed_rejects_predictions_created():
    assert any("predictions_created" in error for error in validate_payload({**summary_payload(valid_counts()), "predictions_created": True}))


def test_seed_rejects_forbidden_target_like_fields():
    assert any("forbidden_target_like_fields_detected" in error for error in validate_payload({**summary_payload(valid_counts()), "forbidden_target_like_fields_detected": True}))


def test_seed_rejects_future_information_fields():
    assert any("future_information_fields_detected" in error for error in validate_payload({**summary_payload(valid_counts()), "future_information_fields_detected": True}))


def test_seed_preview_records_limited_to_10():
    payload = summary_payload({**valid_counts(), "preview_records_count": 11})
    assert any("preview_records_count > 10" in error for error in validate_payload(payload))


def test_seed_manifest_contains_checksums(seed_root: Path):
    build_seed(seed_root)
    manifest = json.loads((seed_root / ALLOWED_FILES[0]).read_text(encoding="utf-8"))
    assert set(manifest["seed_file_checksums"]) == {path.name for path in ALLOWED_FILES[1:]}


def test_seed_provenance_references_v1_84_v1_87_v1_90(seed_root: Path):
    build_seed(seed_root)
    provenance = json.loads((seed_root / ALLOWED_FILES[3]).read_text(encoding="utf-8"))
    assert (provenance["references_v1_84"], provenance["references_v1_87"], provenance["references_v1_90"]) == (True, True, True)


def test_seed_schema_contains_timestamp_fields(seed_root: Path):
    build_seed(seed_root)
    schema = json.loads((seed_root / ALLOWED_FILES[1]).read_text(encoding="utf-8"))
    names = {field["name"] for field in schema["fields"]}
    assert {"event_ts", "available_ts", "decision_ts"} <= names


def test_seed_schema_contains_available_ts_policy(seed_root: Path):
    build_seed(seed_root)
    schema = json.loads((seed_root / ALLOWED_FILES[1]).read_text(encoding="utf-8"))
    assert schema["available_ts_policy"] == "feature_available_ts_lte_decision_ts"


def test_validator_rejects_available_ts_policy_not_applied():
    assert any("available_ts_policy_applied" in error for error in validate_payload({**summary_payload(valid_counts()), "available_ts_policy_applied": False}))


def test_validator_rejects_no_lookahead_policy_not_applied():
    assert any("no_lookahead_policy_applied" in error for error in validate_payload({**summary_payload(valid_counts()), "no_lookahead_policy_applied": False}))


def test_validator_rejects_leakage_detected_true():
    assert any("leakage_detected" in error for error in validate_payload({**summary_payload(valid_counts()), "leakage_detected": True}))


def test_validator_rejects_real_orders_possible_true():
    assert any("real_orders_possible" in error for error in validate_payload({**summary_payload(valid_counts()), "real_orders_possible": True}))


def test_report_index_references_v1_92(report_root: Path):
    errors = validate_report_set(report_root)
    assert not errors


def test_smoke_v1_92_runs_validator_import_and_summary_presence():
    smoke = (PROJECT_ROOT / "scripts/smoke_test_clean_zip.py").read_text(encoding="utf-8")
    assert "validate_mini_research_dataset_seed_v1_92_reports.py" in smoke
    assert "mini_research_dataset_seed_summary_v1_92.json" in smoke


def test_cross_file_alignment_summary_latest_metrics_project_state(report_root: Path):
    latest = json.loads((report_root / "reports/current/latest_metrics.json").read_text(encoding="utf-8"))
    latest["network_executed"] = True
    (report_root / "reports/current/latest_metrics.json").write_text(json.dumps(latest), encoding="utf-8")
    errors = validate_report_set(report_root)
    assert any("latest: network_executed diverges from summary" in error for error in errors)


def test_no_pass_only_tests_in_v1_92():
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    offenders = [
        node.name for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_") and len(node.body) == 1 and isinstance(node.body[0], ast.Pass)
    ]
    assert offenders == []


def test_no_assert_true_or_true_in_v1_92():
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    bad_asserts = [node for node in ast.walk(tree) if isinstance(node, ast.Assert) and isinstance(node.test, ast.Constant) and node.test.value is True]
    bad_or = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or)
        and any(isinstance(value, ast.Constant) and value.value is True for value in node.values)
    ]
    assert bad_asserts == []
    assert bad_or == []


def valid_counts() -> dict:
    return {
        "created_files_count": 5,
        "total_new_data_files_created": 5,
        "total_data_bytes_written": 1,
        "preview_records_count": 1,
        "parquet_created": False,
        "csv_created": False,
        "sqlite_created": False,
        "jsonl_created": False,
        "db_created": False,
        "unapproved_data_write_detected": False,
        "existing_v1_84_files_modified": False,
        "existing_v1_87_files_modified": False,
        "existing_v1_90_files_modified": False,
    }
