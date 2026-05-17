from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pytest

from galapagos.research.causal_feature_readiness import (
    CausalFeatureApprovalGate,
    CausalFeatureDryRun,
    CausalFeatureSchemaDesigner,
    SeedReadinessReader,
)
from galapagos.research.causal_feature_readiness.anti_leakage_feature_guard import scan_forbidden_feature_terms
from galapagos.research.causal_feature_readiness.validator import validate_report_set

PROJECT_ROOT = Path(__file__).resolve().parents[2]
VERSION = "V1.94"
VERSION_SUFFIX = "v1_94"
APPROVAL = "J'approuve V1.95 feature preview materialization ultra-bornée, sans réseau, sans labels, sans targets, sans ML, sans trading."
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
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _seed_payloads() -> dict[str, dict]:
    return {
        "seed_schema.json": {
            "fields": [
                {"name": "available_ts", "type": "string"},
                {"name": "decision_ts", "type": "string"},
                {"name": "event_ts", "type": "string"},
            ],
            "policies": ["available_ts <= decision_ts", "no_lookahead"],
        },
        "seed_preview_records.json": {
            "records": [
                {
                    "available_ts": "2026-01-01T00:00:01Z",
                    "decision_ts": "2026-01-01T00:00:01Z",
                    "event_ts": "2026-01-01T00:00:00Z",
                }
            ]
        },
        "seed_provenance.json": {"sources": ["V1.84", "V1.87.2", "V1.90.1"]},
        "seed_quality_audit.json": {"available_ts_policy": "present", "no_lookahead_policy": "present"},
    }


def _write_seed(root: Path) -> None:
    seed_root = root / SEED_ROOT
    seed_root.mkdir(parents=True, exist_ok=True)
    for name, payload in _seed_payloads().items():
        _write_json(seed_root / name, payload)
    checksums = {name: _sha256(seed_root / name) for name in SEED_FILES if name != "seed_manifest.json"}
    _write_json(seed_root / "seed_manifest.json", {"seed_file_checksums": checksums})


def _base_payload(seed: dict, schema: dict, dryrun: dict, anti: dict, approval: dict) -> dict:
    return {
        "version": VERSION,
        "version_suffix": VERSION_SUFFIX,
        "previous_validated_version": "V1.93.5",
        "reviewed_seed_version": "V1.92.1",
        "post_seed_review_version": "V1.93.5",
        "final_verdict": "V1_94_CAUSAL_FEATURE_READINESS_AND_DRYRUN_PASSED",
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
        "data_directory_writes_allowed": False,
        "data_directory_write_attempted": False,
        "new_data_files_created": False,
        "existing_seed_files_modified": False,
        "no_new_data_directory_writes": True,
        "dataset_created": False,
        "research_dataset_updated": False,
        "network_executed": False,
        "new_network_requests_executed": False,
        "trading_allowed": False,
        "real_orders_possible": False,
        "no_real_trading": True,
        "no_paper_live": True,
        "future_feature_dry_run_max_preview_rows": 10,
        "future_feature_dry_run_max_theoretical_features": 20,
        "release_ready_for_external_review": True,
        "clean_zip_ready_for_external_review": True,
        "smoke_test_passed": True,
        "blocking_reason": None,
        **approval,
        **seed,
        **{k: v for k, v in schema.items() if k.endswith("_defined") or k.endswith("_forbidden")},
        **anti,
    }


@pytest.fixture
def mock_reports(tmp_path: Path) -> Path:
    _write_seed(tmp_path)
    for folder in ["reports/research", "reports/current", "docs"]:
        (tmp_path / folder).mkdir(parents=True, exist_ok=True)
    approval = CausalFeatureApprovalGate().evaluate(APPROVAL)
    seed = SeedReadinessReader(tmp_path).audit()
    schema = CausalFeatureSchemaDesigner().design()
    dryrun = CausalFeatureDryRun().build_preview(schema)
    anti = scan_forbidden_feature_terms({"schema.theoretical_features": schema["theoretical_features"], "dryrun.preview_rows": dryrun["preview_rows"]})
    payload = _base_payload(seed, schema, dryrun, anti, approval)

    reports = {
        f"reports/research/causal_feature_readiness_summary_{VERSION_SUFFIX}.json": payload,
        f"reports/research/causal_feature_schema_design_{VERSION_SUFFIX}.json": schema,
        f"reports/research/causal_feature_dryrun_preview_{VERSION_SUFFIX}.json": dryrun,
        f"reports/research/causal_feature_anti_leakage_audit_{VERSION_SUFFIX}.json": {"version": VERSION, **anti},
        f"reports/research/causal_feature_approval_decision_{VERSION_SUFFIX}.json": {"version": VERSION, **approval},
        f"reports/research/causal_feature_readiness_safety_check_{VERSION_SUFFIX}.json": {"version": VERSION, "safety_check_passed": True},
        f"reports/research/causal_feature_readiness_consistency_check_{VERSION_SUFFIX}.json": {"version": VERSION, "issues": []},
        "reports/current/latest_metrics.json": payload,
        "reports/PROJECT_STATE.json": payload,
        f"reports/release_zip_{VERSION_SUFFIX}.json": {
            "version": VERSION,
            "release_zip_created": True,
            "final_zip_created": True,
            "release_ready_for_external_review": True,
            "clean_zip_ready_for_external_review": True,
            "final_audit_passed": True,
            "final_smoke_passed": True,
            "blocking_reason": None,
        },
        f"reports/zip_audit_{VERSION_SUFFIX}.json": {
            "version": VERSION,
            "clean_zip_ready_for_external_review": True,
            "audit_zip_project_state_version": VERSION,
            "audit_zip_version_parse_correct": True,
            "global_json_finiteness_passed": True,
            "missing_required_files": [],
            "forbidden_count": 0,
        },
        f"reports/zip_smoke_test_{VERSION_SUFFIX}.json": {
            "version": VERSION,
            "smoke_test_passed": True,
            "smoke_failed_count": 0,
            "smoke_passed_count": 3,
            "smoke_commands_count": 3,
            "smoke_commands_not_empty": True,
            "smoke_timeout_detected": False,
            "bounded_smoke_for_v1_94": True,
            "real_orders_possible": False,
            "codex_cli_called": False,
            "holdout_executed": False,
        },
    }
    for relative, content in reports.items():
        _write_json(tmp_path / relative, content)
        (tmp_path / relative).with_suffix(".md").write_text("# Rapport", encoding="utf-8")
    (tmp_path / "reports/REPORT_INDEX.md").write_text("V1.94 v1_94", encoding="utf-8")
    (tmp_path / "docs/code_review_v1_94.md").write_text("Review", encoding="utf-8")
    (tmp_path / "docs/causal_feature_readiness_v1_94.md").write_text("Doc", encoding="utf-8")
    return tmp_path


def _mutate_json(root: Path, relative: str, **updates: object) -> None:
    path = root / relative
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.update(updates)
    _write_json(path, payload)


def _set_state(root: Path, field: str, value: object) -> None:
    for relative in [
        "reports/research/causal_feature_readiness_summary_v1_94.json",
        "reports/current/latest_metrics.json",
        "reports/PROJECT_STATE.json",
    ]:
        _mutate_json(root, relative, **{field: value})


def _errors(root: Path) -> list[str]:
    return validate_report_set(root, VERSION_SUFFIX)


def test_exact_approval_phrase_grants_future_v1_95_only() -> None:
    decision = CausalFeatureApprovalGate().evaluate(APPROVAL)
    assert decision["approval_phrase_match"] is True
    assert decision["v1_95_authorized"] is True
    assert decision["authorized_future_version"] == "V1.95"


def test_wrong_approval_phrase_denies() -> None:
    decision = CausalFeatureApprovalGate().evaluate("wrong")
    assert decision["human_approval_granted"] is False
    assert decision["v1_95_authorized"] is False


def test_approval_does_not_execute_v1_95() -> None:
    decision = CausalFeatureApprovalGate().evaluate(APPROVAL)
    assert decision["v1_95_execution_attempted"] is False


def test_approval_does_not_write_data(mock_reports: Path) -> None:
    assert json.loads((mock_reports / "reports/PROJECT_STATE.json").read_text())["data_directory_write_attempted"] is False


def test_seed_read_only(mock_reports: Path) -> None:
    audit = SeedReadinessReader(mock_reports).audit()
    assert audit["existing_seed_files_modified"] is False
    assert audit["reviewed_seed_files_count"] == 5


def test_feature_schema_design_created() -> None:
    schema = CausalFeatureSchemaDesigner().design()
    assert schema["causal_feature_schema_designed"] is True
    assert 0 < schema["theoretical_features_count"] <= 20


def test_feature_dryrun_preview_created_in_reports_only() -> None:
    preview = CausalFeatureDryRun().build_preview(CausalFeatureSchemaDesigner().design())
    assert preview["feature_dry_run_preview_in_reports_only"] is True


def test_feature_dryrun_does_not_write_data() -> None:
    preview = CausalFeatureDryRun().build_preview(CausalFeatureSchemaDesigner().design())
    assert preview["feature_dry_run_data_write_allowed"] is False


def test_feature_dryrun_preview_rows_limited_to_10() -> None:
    preview = CausalFeatureDryRun().build_preview(CausalFeatureSchemaDesigner().design())
    assert preview["preview_rows_count"] <= 10


def test_feature_dryrun_theoretical_features_limited_to_20() -> None:
    schema = CausalFeatureSchemaDesigner().design()
    assert schema["theoretical_features_count"] <= 20


@pytest.mark.parametrize("term", ["target_return", "label_flag", "prediction_score", "future_return_1h", "pnl_value"])
def test_feature_schema_rejects_forbidden_terms(term: str) -> None:
    schema = CausalFeatureSchemaDesigner().design()
    schema["theoretical_features"].append({"feature_name": term, "expression": term, "description": term})
    scan = scan_forbidden_feature_terms({"schema.theoretical_features": schema["theoretical_features"]})
    assert scan["forbidden_feature_terms_detected"] is True


def test_feature_schema_rejects_target_like_fields() -> None:
    test_feature_schema_rejects_forbidden_terms("target_return")


def test_feature_schema_rejects_label_like_fields() -> None:
    test_feature_schema_rejects_forbidden_terms("label_up_down")


def test_feature_schema_rejects_prediction_like_fields() -> None:
    test_feature_schema_rejects_forbidden_terms("prediction_score")


def test_feature_schema_rejects_future_information_fields() -> None:
    test_feature_schema_rejects_forbidden_terms("future_return_1h")


def test_feature_schema_rejects_pnl_profit_ev_mfe_mae() -> None:
    for term in ["pnl", "profit", "expected_value", "mfe", "mae"]:
        scan = scan_forbidden_feature_terms({"schema": [{"feature_name": term}]})
        assert scan["forbidden_feature_terms_detected"] is True


def test_feature_plan_requires_available_ts() -> None:
    assert CausalFeatureSchemaDesigner().design()["available_ts_policy_defined"] is True


def test_feature_plan_requires_decision_ts() -> None:
    assert CausalFeatureSchemaDesigner().design()["decision_ts_policy_defined"] is True


def test_feature_plan_requires_available_ts_lte_decision_ts_rule() -> None:
    assert CausalFeatureSchemaDesigner().design()["feature_available_ts_lte_decision_ts_rule_defined"] is True


def test_feature_plan_requires_no_lookahead_policy() -> None:
    assert CausalFeatureSchemaDesigner().design()["no_lookahead_policy_defined"] is True


@pytest.mark.parametrize(
    "field",
    [
        "feature_generation_executed",
        "physical_features_created",
        "feature_files_created_in_data",
        "labels_created",
        "targets_created",
        "predictions_created",
        "model_training_executed",
        "ml_signal_validation_executed",
        "data_directory_write_attempted",
        "network_executed",
        "trading_allowed",
        "real_orders_possible",
        "v1_95_execution_attempted",
    ],
)
def test_validator_rejects_false_invariant_when_true(mock_reports: Path, field: str) -> None:
    _set_state(mock_reports, field, True)
    assert _errors(mock_reports)


def test_validator_rejects_feature_generation_executed_true(mock_reports: Path) -> None:
    _set_state(mock_reports, "feature_generation_executed", True)
    assert _errors(mock_reports)


def test_validator_rejects_physical_features_created_true(mock_reports: Path) -> None:
    _set_state(mock_reports, "physical_features_created", True)
    assert _errors(mock_reports)


def test_validator_rejects_feature_files_created_in_data_true(mock_reports: Path) -> None:
    _set_state(mock_reports, "feature_files_created_in_data", True)
    assert _errors(mock_reports)


def test_validator_rejects_labels_created_true(mock_reports: Path) -> None:
    _set_state(mock_reports, "labels_created", True)
    assert _errors(mock_reports)


def test_validator_rejects_targets_created_true(mock_reports: Path) -> None:
    _set_state(mock_reports, "targets_created", True)
    assert _errors(mock_reports)


def test_validator_rejects_predictions_created_true(mock_reports: Path) -> None:
    _set_state(mock_reports, "predictions_created", True)
    assert _errors(mock_reports)


def test_validator_rejects_model_training_executed_true(mock_reports: Path) -> None:
    _set_state(mock_reports, "model_training_executed", True)
    assert _errors(mock_reports)


def test_validator_rejects_ml_signal_validation_executed_true(mock_reports: Path) -> None:
    _set_state(mock_reports, "ml_signal_validation_executed", True)
    assert _errors(mock_reports)


def test_validator_rejects_data_write_attempted_true(mock_reports: Path) -> None:
    _set_state(mock_reports, "data_directory_write_attempted", True)
    assert _errors(mock_reports)


def test_validator_rejects_network_executed_true(mock_reports: Path) -> None:
    _set_state(mock_reports, "network_executed", True)
    assert _errors(mock_reports)


def test_validator_rejects_trading_allowed_true(mock_reports: Path) -> None:
    _set_state(mock_reports, "trading_allowed", True)
    assert _errors(mock_reports)


def test_validator_rejects_real_orders_possible_true(mock_reports: Path) -> None:
    _set_state(mock_reports, "real_orders_possible", True)
    assert _errors(mock_reports)


def test_validator_rejects_v1_95_execution_attempted_true(mock_reports: Path) -> None:
    _set_state(mock_reports, "v1_95_execution_attempted", True)
    assert _errors(mock_reports)


def test_validator_rejects_forbidden_feature_terms_detected_true(mock_reports: Path) -> None:
    _set_state(mock_reports, "forbidden_feature_terms_detected", True)
    _set_state(mock_reports, "forbidden_feature_terms_count", 1)
    assert _errors(mock_reports)


def test_validator_rejects_dryrun_preview_with_future_return(mock_reports: Path) -> None:
    path = mock_reports / "reports/research/causal_feature_dryrun_preview_v1_94.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["preview_rows"][0]["future_return_1h"] = 0.1
    _write_json(path, payload)
    assert _errors(mock_reports)


def test_validator_rejects_schema_with_target_return(mock_reports: Path) -> None:
    path = mock_reports / "reports/research/causal_feature_schema_design_v1_94.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["theoretical_features"].append({"feature_name": "target_return", "expression": "target_return"})
    _write_json(path, payload)
    assert _errors(mock_reports)


def test_validator_rejects_release_final_smoke_false(mock_reports: Path) -> None:
    _mutate_json(mock_reports, "reports/release_zip_v1_94.json", final_smoke_passed=False)
    assert _errors(mock_reports)


def test_validator_rejects_zip_audit_project_state_version_mismatch(mock_reports: Path) -> None:
    _mutate_json(mock_reports, "reports/zip_audit_v1_94.json", audit_zip_project_state_version="V1.93.5")
    assert _errors(mock_reports)


def test_validator_rejects_zip_smoke_failed_count_positive(mock_reports: Path) -> None:
    _mutate_json(mock_reports, "reports/zip_smoke_test_v1_94.json", smoke_failed_count=1)
    assert _errors(mock_reports)


def test_report_index_references_v1_94(mock_reports: Path) -> None:
    assert "V1.94" in (mock_reports / "reports/REPORT_INDEX.md").read_text(encoding="utf-8")


def test_smoke_v1_94_runs_validator_import_and_summary_presence() -> None:
    content = (PROJECT_ROOT / "scripts/smoke_test_clean_zip.py").read_text(encoding="utf-8")
    assert "validate_causal_feature_readiness_v1_94_reports.py" in content
    assert "galapagos.research.causal_feature_readiness" in content
    assert "causal_feature_readiness_summary_v1_94.json" in content


def test_cross_file_alignment_summary_latest_metrics_project_state(mock_reports: Path) -> None:
    assert not _errors(mock_reports)
    _mutate_json(mock_reports, "reports/current/latest_metrics.json", version="V1.93.5")
    assert _errors(mock_reports)


def test_no_pass_only_tests_in_v1_94() -> None:
    tree = ast.parse((PROJECT_ROOT / "tests/research/test_causal_feature_readiness_v1_94.py").read_text(encoding="utf-8"))
    offenders = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name.startswith("test_") and len(node.body) == 1 and isinstance(node.body[0], ast.Pass)]
    assert offenders == []


def test_no_assert_true_or_true_in_v1_94() -> None:
    tree = ast.parse((PROJECT_ROOT / "tests/research/test_causal_feature_readiness_v1_94.py").read_text(encoding="utf-8"))
    bad_asserts = [node.lineno for node in ast.walk(tree) if isinstance(node, ast.Assert) and isinstance(node.test, ast.Constant) and node.test.value is True]
    bad_or = [node.lineno for node in ast.walk(tree) if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or) and any(isinstance(value, ast.Constant) and value.value is True for value in node.values)]
    assert bad_asserts == []
    assert bad_or == []
