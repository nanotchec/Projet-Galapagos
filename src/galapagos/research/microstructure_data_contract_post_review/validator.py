from __future__ import annotations

from typing import Any

from .safety_guard import PostReviewSafetyGuard


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors = PostReviewSafetyGuard().check(payload)["safety_issues"]
    expected = {
        "post_materialization_review_executed": True,
        "review_only": True,
        "reports_only": True,
        "materialization_executed": False,
        "new_materialization_executed": False,
        "data_contract_actual_write_executed": False,
        "data_directory_write_attempted": False,
        "new_data_files_created": False,
        "existing_data_files_modified": False,
        "no_new_data_directory_writes": True,
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
        "trading_allowed": False,
        "real_orders_possible": False,
        "no_real_trading": True,
        "no_paper_live": True,
        "ml_signal_validation_executed": False,
        "release_ready_for_external_review": True,
        "smoke_test_passed": True,
        "clean_zip_ready_for_external_review": True,
    }
    for field, value in expected.items():
        if payload.get(field) is not value:
            errors.append(f"{field} != {value!r}")
    return errors
