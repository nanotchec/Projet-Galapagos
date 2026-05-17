from __future__ import annotations

import ast
import json
import shutil
from pathlib import Path

import pytest

from galapagos.research.mini_research_dataset_seed import MiniResearchDatasetSeedBuilder, SeedBuildError
from galapagos.research.mini_research_dataset_seed.physical_auditor import (
    V1_84_FILES,
    V1_87_FILES,
    V1_90_FILES,
    V1_92_FILES,
    sha256_file,
)
from galapagos.research.mini_research_dataset_seed.semantic_scan import scan_physical_seed_semantics
from galapagos.research.mini_research_dataset_seed.validator import validate_payload, validate_report_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCOPE = "mini_research_dataset_seed_ultra_bounded_no_network_no_full_dataset_no_ml_no_trading"


@pytest.fixture
def seed_root(tmp_path: Path) -> Path:
    for rel in [*V1_84_FILES, *V1_87_FILES, *V1_90_FILES]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PROJECT_ROOT / rel, target)
    build_seed(tmp_path)
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
    return MiniResearchDatasetSeedBuilder(root).build(
        approval=approval(),
        design=design(),
        anti_leakage_plan=anti_plan(),
        version="V1.92.1",
    )


def recompute_manifest(root: Path) -> None:
    manifest_path = root / V1_92_FILES[0]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["seed_file_checksums"] = {rel.name: sha256_file(root / rel) for rel in V1_92_FILES[1:]}
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def mutate_json(root: Path, rel: Path, key: str, value: object) -> None:
    path = root / rel
    data = json.loads(path.read_text(encoding="utf-8"))
    data[key] = value
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    recompute_manifest(root)


def payload_base(**overrides: object) -> dict:
    payload = {
        "version": "V1.92.1",
        "final_verdict": "V1_92_1_PHYSICAL_SEED_SEMANTIC_GUARD_PASSED",
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
        "allowed_data_write_root": "data/research/dataset_seed/v1_92/",
        "unapproved_data_write_detected": False,
        "total_new_data_files_created": 5,
        "created_files_count": 5,
        "total_data_bytes_written": 100,
        "preview_records_count": 3,
        "existing_v1_84_files_modified": False,
        "existing_v1_87_files_modified": False,
        "existing_v1_90_files_modified": False,
        "parquet_created": False,
        "csv_created": False,
        "sqlite_created": False,
        "jsonl_created": False,
        "db_created": False,
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
        "physical_seed_semantic_scan_executed": True,
        "forbidden_seed_terms_detected": False,
        "forbidden_seed_terms_count": 0,
        "forbidden_seed_term_occurrences": [],
        "target_like_fields_detected": False,
        "label_like_fields_detected": False,
        "prediction_like_fields_detected": False,
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
        "release_ready_for_external_review": True,
        "clean_zip_ready_for_external_review": True,
        "smoke_test_passed": True,
        "blocking_reason": None,
    }
    payload.update(overrides)
    return payload


def test_semantic_scan_rejects_target_return_in_seed_schema_even_with_recomputed_checksum(seed_root: Path):
    mutate_json(seed_root, V1_92_FILES[1], "target_return", "blocked")
    result = scan_physical_seed_semantics(seed_root)
    assert result["forbidden_seed_terms_detected"] is True
    assert any(item["matched_term"] == "target" for item in result["forbidden_seed_term_occurrences"])


def test_semantic_scan_rejects_future_return_in_preview_records_even_with_recomputed_checksum(seed_root: Path):
    mutate_json(seed_root, V1_92_FILES[2], "future_return_1h", 0.01)
    result = scan_physical_seed_semantics(seed_root)
    assert result["future_information_fields_detected"] is True


def test_semantic_scan_rejects_prediction_score_in_seed_manifest(seed_root: Path):
    mutate_json(seed_root, V1_92_FILES[0], "prediction_score", "blocked")
    assert scan_physical_seed_semantics(seed_root)["prediction_like_fields_detected"] is True


def test_semantic_scan_rejects_label_up_down_in_seed_provenance(seed_root: Path):
    mutate_json(seed_root, V1_92_FILES[3], "label_up_down", "blocked")
    assert scan_physical_seed_semantics(seed_root)["label_like_fields_detected"] is True


def test_semantic_scan_rejects_expected_value_in_quality_audit(seed_root: Path):
    mutate_json(seed_root, V1_92_FILES[4], "expected_value", "blocked")
    result = scan_physical_seed_semantics(seed_root)
    assert any(item["matched_term"] == "expected_value" for item in result["forbidden_seed_term_occurrences"])


def test_semantic_scan_rejects_mfe_mae_fields(seed_root: Path):
    mutate_json(seed_root, V1_92_FILES[4], "mfe", "blocked")
    mutate_json(seed_root, V1_92_FILES[4], "mae", "blocked")
    terms = {item["matched_term"] for item in scan_physical_seed_semantics(seed_root)["forbidden_seed_term_occurrences"]}
    assert {"mfe", "mae"} <= terms


def test_semantic_scan_reports_occurrence_file_and_json_path(seed_root: Path):
    mutate_json(seed_root, V1_92_FILES[1], "target_return", "blocked")
    occurrence = scan_physical_seed_semantics(seed_root)["forbidden_seed_term_occurrences"][0]
    assert occurrence["file"].endswith("seed_schema.json")
    assert occurrence["json_path"] == "$.target_return"


def test_validator_rejects_forbidden_seed_terms_detected_true():
    assert any("forbidden_seed_terms_detected" in error for error in validate_payload(payload_base(forbidden_seed_terms_detected=True)))


def test_validator_rejects_forbidden_seed_terms_count_positive():
    assert any("forbidden_seed_terms_count" in error for error in validate_payload(payload_base(forbidden_seed_terms_count=1)))


def test_validator_rejects_non_empty_forbidden_seed_term_occurrences():
    payload = payload_base(forbidden_seed_term_occurrences=[{"file": "x", "json_path": "$", "offending_key_or_value": "target", "matched_term": "target"}])
    assert any("forbidden_seed_term_occurrences" in error for error in validate_payload(payload))


def test_validator_rejects_target_like_fields_detected_true():
    assert any("target_like_fields_detected" in error for error in validate_payload(payload_base(target_like_fields_detected=True)))


def test_validator_rejects_future_information_fields_detected_true():
    assert any("future_information_fields_detected" in error for error in validate_payload(payload_base(future_information_fields_detected=True)))


def test_validator_rejects_label_like_fields_detected_true():
    assert any("label_like_fields_detected" in error for error in validate_payload(payload_base(label_like_fields_detected=True)))


def test_validator_rejects_prediction_like_fields_detected_true():
    assert any("prediction_like_fields_detected" in error for error in validate_payload(payload_base(prediction_like_fields_detected=True)))


def test_seed_still_writes_exactly_five_json_files(seed_root: Path):
    files = sorted((seed_root / "data/research/dataset_seed/v1_92").glob("*"))
    assert len(files) == 5
    assert all(path.suffix == ".json" for path in files)


def test_seed_preview_records_limited_to_10(seed_root: Path):
    preview = json.loads((seed_root / V1_92_FILES[2]).read_text(encoding="utf-8"))
    assert len(preview["records"]) <= 10


def test_seed_rejects_network_executed():
    assert any("network_executed" in error for error in validate_payload(payload_base(network_executed=True)))


def test_seed_rejects_dataset_created():
    assert any("dataset_created" in error for error in validate_payload(payload_base(dataset_created=True)))


def test_seed_rejects_real_orders_possible():
    assert any("real_orders_possible" in error for error in validate_payload(payload_base(real_orders_possible=True)))


def test_report_index_references_v1_92_1():
    assert "v1_92_1" in (PROJECT_ROOT / "scripts/run_mini_research_dataset_seed_v1_92_1.py").read_text(encoding="utf-8")


def test_smoke_v1_92_1_runs_validator_import_and_summary_presence():
    smoke = (PROJECT_ROOT / "scripts/smoke_test_clean_zip.py").read_text(encoding="utf-8")
    assert "validate_mini_research_dataset_seed_v1_92_1_reports.py" in smoke
    assert "mini_research_dataset_seed_summary_v1_92_1.json" in smoke


def test_no_pass_only_tests_in_v1_92_1():
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    offenders = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name.startswith("test_")
        and len(node.body) == 1
        and isinstance(node.body[0], ast.Pass)
    ]
    assert offenders == []


def test_no_assert_true_or_true_in_v1_92_1():
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    bad_asserts = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Assert) and isinstance(node.test, ast.Constant) and node.test.value is True
    ]
    bad_or = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.BoolOp)
        and isinstance(node.op, ast.Or)
        and any(isinstance(value, ast.Constant) and value.value is True for value in node.values)
    ]
    assert bad_asserts == []
    assert bad_or == []
