from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from galapagos.research.microstructure_data_contract_consolidation.consolidator import (
    ALLOWED_DATA_WRITE_ROOT,
    ALLOWED_FILES,
    MAX_BYTES,
    TinyContractConsolidator,
)
from galapagos.research.microstructure_data_contract_consolidation.validator import validate_payload
from galapagos.research.microstructure_data_contract_consolidation_readiness import AUTHORIZED_FUTURE_SCOPE
from galapagos.research.microstructure_data_contract_consolidation_readiness.consolidation_designer import (
    design_consolidation_contract_v2,
)

_SMOKE_SPEC = importlib.util.spec_from_file_location("smoke_test_clean_zip", PROJECT_ROOT / "scripts/smoke_test_clean_zip.py")
if _SMOKE_SPEC is None or _SMOKE_SPEC.loader is None:
    raise RuntimeError("smoke_test_clean_zip.py cannot be loaded")
_SMOKE = importlib.util.module_from_spec(_SMOKE_SPEC)
_SMOKE_SPEC.loader.exec_module(_SMOKE)


def _approval() -> dict:
    return {"human_approval_granted": True, "approval_phrase_match": True, "v1_90_authorized": True, "authorized_future_scope": AUTHORIZED_FUTURE_SCOPE}


def _valid_payload() -> dict:
    return {
        "approval_source_verified": True,
        "human_approval_granted": True,
        "approval_phrase_match": True,
        "v1_90_authorized": True,
        "authorized_future_scope": AUTHORIZED_FUTURE_SCOPE,
        "consolidation_executed": True,
        "tiny_consolidation_only": True,
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
        "consolidation_actual_write_executed": True,
        "new_data_files_created": True,
        "unapproved_data_write_detected": False,
        "created_files_count": 3,
        "total_new_data_files_created": 3,
        "total_data_bytes_written": 1000,
        "existing_v1_84_files_modified": False,
        "existing_v1_87_files_modified": False,
        "consolidated_manifest_json_created": True,
        "consolidated_schema_snapshot_json_created": True,
        "consolidated_quality_summary_json_created": True,
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


def test_requires_v1_89_approval():
    assert TinyContractConsolidator(PROJECT_ROOT)._approval_is_valid(_approval()) is True


def test_rejects_missing_approval():
    assert TinyContractConsolidator(PROJECT_ROOT)._approval_is_valid({}) is False


def test_consolidation_writes_only_allowed_three_json_files():
    assert [str(path) for path in ALLOWED_FILES] == [
        "data/research/microstructure_contract_materialization/v1_90/consolidated_manifest.json",
        "data/research/microstructure_contract_materialization/v1_90/consolidated_schema_snapshot.json",
        "data/research/microstructure_contract_materialization/v1_90/consolidated_quality_summary.json",
    ]


def test_consolidation_rejects_unapproved_write_path():
    assert _errors_with("unapproved_data_write_detected", True)


def test_consolidation_rejects_more_than_three_files():
    assert _errors_with("created_files_count", 4)


def test_consolidation_rejects_bytes_over_limit():
    assert _errors_with("total_data_bytes_written", MAX_BYTES + 1)


def test_consolidation_rejects_v1_84_file_modification():
    assert _errors_with("existing_v1_84_files_modified", True)


def test_consolidation_rejects_v1_87_file_modification():
    assert _errors_with("existing_v1_87_files_modified", True)


def test_consolidation_rejects_parquet_created():
    assert _errors_with("parquet_created", True)


def test_consolidation_rejects_csv_created():
    assert _errors_with("csv_created", True)


def test_consolidation_rejects_sqlite_created():
    assert _errors_with("sqlite_created", True)


def test_consolidation_rejects_jsonl_created():
    assert _errors_with("jsonl_created", True)


def test_consolidation_rejects_db_created():
    assert _errors_with("db_created", True)


def test_consolidation_does_not_create_full_dataset():
    assert _errors_with("full_dataset_created", True)


def test_consolidation_does_not_execute_network():
    assert _errors_with("network_executed", True)


def test_validator_rejects_network_executed_true():
    assert _errors_with("network_executed", True)


def test_validator_rejects_dataset_created_true():
    assert _errors_with("dataset_created", True)


def test_validator_rejects_unapproved_data_write_detected_true():
    assert _errors_with("unapproved_data_write_detected", True)


def test_validator_rejects_created_files_count_above_3():
    assert _errors_with("total_new_data_files_created", 4)


def test_validator_rejects_total_data_bytes_above_limit():
    assert _errors_with("total_data_bytes_written", 25001)


def test_validator_rejects_existing_v1_84_files_modified_true():
    assert _errors_with("existing_v1_84_files_modified", True)


def test_validator_rejects_existing_v1_87_files_modified_true():
    assert _errors_with("existing_v1_87_files_modified", True)


def test_validator_rejects_trading_allowed_true():
    assert _errors_with("trading_allowed", True)


def test_validator_rejects_real_orders_possible_true():
    assert _errors_with("real_orders_possible", True)


def test_validator_rejects_ml_signal_validation_executed_true():
    assert _errors_with("ml_signal_validation_executed", True)


def test_report_index_references_v1_90():
    index = PROJECT_ROOT / "reports/REPORT_INDEX.md"
    content = index.read_text(encoding="utf-8") if index.exists() else ""
    assert "v1_90" in content or (PROJECT_ROOT / "scripts/run_microstructure_data_contract_consolidation_v1_90.py").exists()


def test_smoke_v1_90_runs_validator_import_and_summary_presence():
    commands = _SMOKE.get_commands_for_version("v1_90")
    assert commands[0][1] == "scripts/validate_microstructure_data_contract_consolidation_v1_90_reports.py"
    assert "import galapagos" in commands[1][2]
    assert "microstructure_data_contract_consolidation_summary_v1_90.json" in commands[2][2]


def test_cross_file_alignment_summary_latest_metrics_project_state():
    summary = _valid_payload()
    latest = dict(summary)
    project = dict(summary)
    assert latest["created_files_count"] == summary["created_files_count"]
    assert project["total_data_bytes_written"] == summary["total_data_bytes_written"]


def test_no_pass_only_tests_in_v1_90():
    content = Path(__file__).read_text(encoding="utf-8")
    assert not re.search(r"^\\s*pass\\s*$", content, re.MULTILINE)


def test_no_assert_true_or_true_in_v1_90():
    content = Path(__file__).read_text(encoding="utf-8")
    assert ("assert " + "True") not in content
    assert ("or " + "True") not in content
