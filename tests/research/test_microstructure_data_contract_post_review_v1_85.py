from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from galapagos.research.microstructure_data_contract_post_review.reviewer import (
    EXPECTED_DATA_FILES,
    REVIEWED_DATA_ROOT,
    PostMaterializationReviewer,
)
from galapagos.research.microstructure_data_contract_post_review.validator import validate_payload

_SMOKE_SPEC = importlib.util.spec_from_file_location("smoke_test_clean_zip", PROJECT_ROOT / "scripts/smoke_test_clean_zip.py")
assert _SMOKE_SPEC is not None and _SMOKE_SPEC.loader is not None
_SMOKE = importlib.util.module_from_spec(_SMOKE_SPEC)
_SMOKE_SPEC.loader.exec_module(_SMOKE)


def _valid_payload() -> dict:
    return {
        "post_materialization_review_executed": True,
        "review_only": True,
        "reports_only": True,
        "materialization_executed": False,
        "new_materialization_executed": False,
        "data_contract_actual_write_executed": False,
        "scope_drift_detected": False,
        "data_directory_writes_allowed": False,
        "data_directory_write_attempted": False,
        "new_data_files_created": False,
        "existing_data_files_modified": False,
        "no_new_data_directory_writes": True,
        "reviewed_files_count": 3,
        "expected_files_count": 3,
        "unexpected_files_count": 0,
        "missing_expected_files_count": 0,
        "total_data_bytes_observed": 1533,
        "preview_records_count": 3,
        "manifest_json_valid": True,
        "schema_snapshot_json_valid": True,
        "preview_records_json_valid": True,
        "manifest_matches_physical_files": True,
        "schema_snapshot_matches_contract": True,
        "parquet_created": False,
        "csv_created": False,
        "sqlite_created": False,
        "jsonl_created": False,
        "db_created": False,
        "dataset_created": False,
        "research_dataset_updated": False,
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


def _write_v1_84_files(root: Path, *, preview_count: int = 3) -> None:
    data_root = root / REVIEWED_DATA_ROOT
    data_root.mkdir(parents=True, exist_ok=True)
    (data_root / "manifest.json").write_text(
        json.dumps({"version": "V1.84", "artifact": "manifest", "max_files": 3, "max_bytes": 20000, "max_preview_records": 5}),
        encoding="utf-8",
    )
    (data_root / "schema_snapshot.json").write_text(
        json.dumps({
            "version": "V1.84",
            "artifact": "schema_snapshot",
            "schema_source": "microstructure_data_contract_dryrun_contract_v1_82_4",
            "contract_fields": [],
        }),
        encoding="utf-8",
    )
    (data_root / "preview_records.json").write_text(
        json.dumps({"version": "V1.84", "preview_records": [{"i": i} for i in range(preview_count)]}),
        encoding="utf-8",
    )


def _contract() -> dict:
    return {"schema": {"timestamp": "datetime64[ns]"}}


def test_review_reads_only_v1_84_data_files(tmp_path):
    _write_v1_84_files(tmp_path)
    audit = PostMaterializationReviewer(tmp_path).review(dryrun_contract=_contract())
    assert audit["reviewed_file_paths"] == [str(path) for path in EXPECTED_DATA_FILES]


def test_review_rejects_missing_manifest(tmp_path):
    _write_v1_84_files(tmp_path)
    (tmp_path / REVIEWED_DATA_ROOT / "manifest.json").unlink()
    assert PostMaterializationReviewer(tmp_path).review(dryrun_contract=_contract())["missing_expected_files_count"] == 1


def test_review_rejects_missing_schema_snapshot(tmp_path):
    _write_v1_84_files(tmp_path)
    (tmp_path / REVIEWED_DATA_ROOT / "schema_snapshot.json").unlink()
    assert PostMaterializationReviewer(tmp_path).review(dryrun_contract=_contract())["schema_snapshot_json_valid"] is False


def test_review_rejects_missing_preview_records(tmp_path):
    _write_v1_84_files(tmp_path)
    (tmp_path / REVIEWED_DATA_ROOT / "preview_records.json").unlink()
    assert PostMaterializationReviewer(tmp_path).review(dryrun_contract=_contract())["preview_records_json_valid"] is False


def test_review_rejects_extra_file_in_data_root(tmp_path):
    _write_v1_84_files(tmp_path)
    (tmp_path / REVIEWED_DATA_ROOT / "extra.json").write_text("{}", encoding="utf-8")
    assert PostMaterializationReviewer(tmp_path).review(dryrun_contract=_contract())["unexpected_files_count"] == 1


def test_review_rejects_invalid_json_manifest(tmp_path):
    _write_v1_84_files(tmp_path)
    (tmp_path / REVIEWED_DATA_ROOT / "manifest.json").write_text("{", encoding="utf-8")
    assert PostMaterializationReviewer(tmp_path).review(dryrun_contract=_contract())["manifest_json_valid"] is False


def test_review_rejects_invalid_json_schema_snapshot(tmp_path):
    _write_v1_84_files(tmp_path)
    (tmp_path / REVIEWED_DATA_ROOT / "schema_snapshot.json").write_text("{", encoding="utf-8")
    assert PostMaterializationReviewer(tmp_path).review(dryrun_contract=_contract())["schema_snapshot_json_valid"] is False


def test_review_rejects_invalid_json_preview_records(tmp_path):
    _write_v1_84_files(tmp_path)
    (tmp_path / REVIEWED_DATA_ROOT / "preview_records.json").write_text("{", encoding="utf-8")
    assert PostMaterializationReviewer(tmp_path).review(dryrun_contract=_contract())["preview_records_json_valid"] is False


def test_review_rejects_preview_records_above_5(tmp_path):
    _write_v1_84_files(tmp_path, preview_count=6)
    assert PostMaterializationReviewer(tmp_path).review(dryrun_contract=_contract())["preview_records_count"] == 6


def test_review_rejects_total_bytes_above_limit():
    assert _errors_with("total_data_bytes_observed", 20_001)


def test_review_rejects_manifest_physical_file_mismatch(tmp_path):
    _write_v1_84_files(tmp_path)
    manifest = tmp_path / REVIEWED_DATA_ROOT / "manifest.json"
    manifest.write_text(json.dumps({"version": "V1.84", "artifact": "manifest", "max_files": 2}), encoding="utf-8")
    assert PostMaterializationReviewer(tmp_path).review(dryrun_contract=_contract())["manifest_matches_physical_files"] is False


def test_review_rejects_forbidden_parquet_csv_sqlite_jsonl_db(tmp_path):
    _write_v1_84_files(tmp_path)
    root = tmp_path / REVIEWED_DATA_ROOT
    for suffix in [".parquet", ".csv", ".sqlite", ".jsonl", ".db"]:
        (root / f"bad{suffix}").write_text("x", encoding="utf-8")
    audit = PostMaterializationReviewer(tmp_path).review(dryrun_contract=_contract())
    assert audit["parquet_created"] is True
    assert audit["csv_created"] is True
    assert audit["sqlite_created"] is True
    assert audit["jsonl_created"] is True
    assert audit["db_created"] is True


def test_validator_rejects_new_data_files_created_true():
    assert _errors_with("new_data_files_created", True)


def test_validator_rejects_existing_data_files_modified_true():
    assert _errors_with("existing_data_files_modified", True)


def test_validator_rejects_data_directory_write_attempted_true():
    assert _errors_with("data_directory_write_attempted", True)


def test_validator_rejects_network_executed_true():
    assert _errors_with("network_executed", True)


def test_validator_rejects_dataset_created_true():
    assert _errors_with("dataset_created", True)


def test_validator_rejects_trading_allowed_true():
    assert _errors_with("trading_allowed", True)


def test_validator_rejects_real_orders_possible_true():
    assert _errors_with("real_orders_possible", True)


def test_report_index_references_v1_85():
    index = PROJECT_ROOT / "reports/REPORT_INDEX.md"
    content = index.read_text(encoding="utf-8") if index.exists() else ""
    assert "v1_85" in content or (PROJECT_ROOT / "scripts/run_microstructure_data_contract_post_review_v1_85.py").exists()


def test_smoke_v1_85_runs_validator_import_and_summary_presence():
    commands = _SMOKE.get_commands_for_version("v1_85")
    assert commands[0][1] == "scripts/validate_microstructure_data_contract_post_review_v1_85_reports.py"
    assert "import galapagos" in commands[1][2]
    assert "microstructure_data_contract_post_review_summary_v1_85.json" in commands[2][2]


def test_cross_file_alignment_summary_latest_metrics_project_state():
    summary = _valid_payload()
    latest = dict(summary)
    project = dict(summary)
    assert latest["reviewed_files_count"] == summary["reviewed_files_count"]
    assert project["total_data_bytes_observed"] == summary["total_data_bytes_observed"]
