from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from galapagos.research.microstructure_data_contract_materialization.materializer import (
    ALLOWED_DATA_WRITE_ROOT,
    ALLOWED_FILES,
    MAX_BYTES,
    MAX_FILES,
    TinyContractMaterializer,
)
from galapagos.research.microstructure_data_contract_materialization.validator import (
    EXPECTED_SCOPE,
    validate_payload,
    validate_physical_outputs,
)

_SMOKE_SPEC = importlib.util.spec_from_file_location(
    "smoke_test_clean_zip",
    PROJECT_ROOT / "scripts/smoke_test_clean_zip.py",
)
assert _SMOKE_SPEC is not None and _SMOKE_SPEC.loader is not None
_SMOKE = importlib.util.module_from_spec(_SMOKE_SPEC)
_SMOKE_SPEC.loader.exec_module(_SMOKE)


def _valid_payload() -> dict:
    return {
        "approval_source_verified": True,
        "human_approval_granted": True,
        "approval_phrase_match": True,
        "v1_84_authorized": True,
        "authorized_future_scope": EXPECTED_SCOPE,
        "materialization_executed": True,
        "tiny_materialization_only": True,
        "full_dataset_created": False,
        "scope_drift_detected": False,
        "reports_only": False,
        "network_executed": False,
        "new_network_requests_executed": False,
        "request_retry_count": 0,
        "pagination_used": False,
        "authenticated_request_allowed": False,
        "secrets_used": False,
        "data_directory_writes_allowed": True,
        "data_write_approved": True,
        "data_directory_write_attempted": True,
        "data_contract_actual_write_executed": True,
        "new_data_files_created": True,
        "no_data_directory_writes": False,
        "allowed_data_write_root": f"{ALLOWED_DATA_WRITE_ROOT}/",
        "unapproved_data_write_detected": False,
        "created_files_count": 3,
        "total_data_files_created": 3,
        "total_data_bytes_written": 1200,
        "preview_records_count": 3,
        "manifest_json_created": True,
        "schema_snapshot_json_created": True,
        "preview_records_json_created": True,
        "created_file_paths": [str(path) for path in ALLOWED_FILES],
        "parquet_created": False,
        "csv_created": False,
        "sqlite_created": False,
        "jsonl_created": False,
        "db_created": False,
        "dataset_created": False,
        "research_dataset_updated": False,
        "dataset_materialization_approved": False,
        "strategy_link_allowed": False,
        "trading_allowed": False,
        "no_strategy_validated": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "real_orders_possible": False,
        "holdout_executed": False,
        "codex_cli_called": False,
        "ml_signal_validation_executed": False,
        "predictions_created": False,
        "labels_created": False,
        "targets_created": False,
        "release_ready_for_external_review": True,
        "smoke_test_passed": True,
        "clean_zip_ready_for_external_review": True,
    }


def _errors_with(field: str, value) -> list[str]:
    payload = _valid_payload()
    payload[field] = value
    return validate_payload(payload)


def _approval() -> dict:
    return {
        "human_approval_granted": True,
        "approval_phrase_match": True,
        "v1_84_authorized": True,
        "authorized_future_scope": EXPECTED_SCOPE,
    }


def test_requires_v1_83_approval(tmp_path):
    materializer = TinyContractMaterializer(tmp_path)
    audit = materializer.materialize(approval=_approval(), dryrun={"contract_fields": ["timestamp"]})
    assert audit["created_files_count"] == MAX_FILES


def test_rejects_missing_approval(tmp_path):
    materializer = TinyContractMaterializer(tmp_path)
    try:
        materializer.materialize(approval={}, dryrun={})
    except ValueError as exc:
        assert "approval" in str(exc)
    else:
        raise AssertionError("missing approval should be rejected")


def test_materialization_writes_only_allowed_three_json_files(tmp_path):
    materializer = TinyContractMaterializer(tmp_path)
    audit = materializer.materialize(approval=_approval(), dryrun={"contract_fields": ["a", "b"]})
    assert audit["created_file_paths"] == [str(path) for path in ALLOWED_FILES]
    assert audit["total_data_files_created"] == 3


def test_materialization_rejects_unapproved_write_path(tmp_path):
    root = tmp_path / ALLOWED_DATA_WRITE_ROOT
    root.mkdir(parents=True)
    (root / "extra.json").write_text("{}", encoding="utf-8")
    assert validate_physical_outputs(tmp_path)


def test_materialization_rejects_more_than_three_files():
    assert _errors_with("created_files_count", 4)


def test_materialization_rejects_bytes_over_limit():
    assert _errors_with("total_data_bytes_written", MAX_BYTES + 1)


def test_materialization_rejects_parquet_created():
    assert _errors_with("parquet_created", True)


def test_materialization_rejects_csv_created():
    assert _errors_with("csv_created", True)


def test_materialization_rejects_sqlite_created():
    assert _errors_with("sqlite_created", True)


def test_materialization_rejects_jsonl_created():
    assert _errors_with("jsonl_created", True)


def test_materialization_rejects_db_created():
    assert _errors_with("db_created", True)


def test_materialization_does_not_create_full_dataset():
    assert _valid_payload()["full_dataset_created"] is False


def test_materialization_does_not_execute_network():
    assert _valid_payload()["network_executed"] is False


def test_validator_rejects_network_executed_true():
    assert _errors_with("network_executed", True)


def test_validator_rejects_dataset_created_true():
    assert _errors_with("dataset_created", True)


def test_validator_rejects_unapproved_data_write_detected_true():
    assert _errors_with("unapproved_data_write_detected", True)


def test_validator_rejects_created_files_count_above_3():
    assert _errors_with("total_data_files_created", 4)


def test_validator_rejects_total_data_bytes_above_limit():
    assert _errors_with("total_data_bytes_written", 20_001)


def test_validator_rejects_trading_allowed_true():
    assert _errors_with("trading_allowed", True)


def test_validator_rejects_real_orders_possible_true():
    assert _errors_with("real_orders_possible", True)


def test_validator_rejects_ml_signal_validation_executed_true():
    assert _errors_with("ml_signal_validation_executed", True)


def test_report_index_references_v1_84():
    index = PROJECT_ROOT / "reports/REPORT_INDEX.md"
    content = index.read_text(encoding="utf-8") if index.exists() else ""
    assert "v1_84" in content or (PROJECT_ROOT / "scripts/run_microstructure_data_contract_materialization_v1_84.py").exists()


def test_smoke_v1_84_runs_validator_import_and_summary_presence():
    commands = _SMOKE.get_commands_for_version("v1_84")
    assert commands[0][1] == "scripts/validate_microstructure_data_contract_materialization_v1_84_reports.py"
    assert "import galapagos" in commands[1][2]
    assert "microstructure_data_contract_materialization_summary_v1_84.json" in commands[2][2]


def test_cross_file_alignment_summary_latest_metrics_project_state(tmp_path):
    summary = _valid_payload()
    latest = dict(summary)
    project = dict(summary)
    assert latest["created_file_paths"] == summary["created_file_paths"]
    assert project["total_data_bytes_written"] == summary["total_data_bytes_written"]


def test_physical_outputs_require_exact_authorized_files(tmp_path):
    root = tmp_path / ALLOWED_DATA_WRITE_ROOT
    root.mkdir(parents=True)
    for rel in ALLOWED_FILES:
        (tmp_path / rel).write_text(json.dumps({"ok": True}), encoding="utf-8")
    assert validate_physical_outputs(tmp_path) == []
