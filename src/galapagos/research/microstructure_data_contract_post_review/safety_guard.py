from __future__ import annotations

from typing import Any


EXPECTED_TRUE = [
    "post_materialization_review_executed",
    "review_only",
    "reports_only",
    "no_new_data_directory_writes",
    "manifest_json_valid",
    "schema_snapshot_json_valid",
    "preview_records_json_valid",
    "manifest_matches_physical_files",
    "schema_snapshot_matches_contract",
    "no_strategy_validated",
    "no_paper_live",
    "no_real_trading",
]

EXPECTED_FALSE = [
    "materialization_executed",
    "new_materialization_executed",
    "data_contract_actual_write_executed",
    "scope_drift_detected",
    "data_directory_writes_allowed",
    "data_directory_write_attempted",
    "new_data_files_created",
    "existing_data_files_modified",
    "parquet_created",
    "csv_created",
    "sqlite_created",
    "jsonl_created",
    "db_created",
    "dataset_created",
    "research_dataset_updated",
    "network_executed",
    "new_network_requests_executed",
    "pagination_used",
    "authenticated_request_allowed",
    "secrets_used",
    "strategy_link_allowed",
    "trading_allowed",
    "real_orders_possible",
    "holdout_executed",
    "codex_cli_called",
    "ml_signal_validation_executed",
    "predictions_created",
    "labels_created",
    "targets_created",
]


class PostReviewSafetyGuard:
    """Checks the V1.85 review remains reports-only and read-only over data."""

    def check(self, payload: dict[str, Any]) -> dict[str, Any]:
        issues: list[str] = []
        for field in EXPECTED_TRUE:
            if payload.get(field) is not True:
                issues.append(f"{field} != true")
        for field in EXPECTED_FALSE:
            if payload.get(field) is not False:
                issues.append(f"{field} != false")
        if payload.get("request_retry_count") != 0:
            issues.append("request_retry_count != 0")
        if payload.get("reviewed_files_count") != 3:
            issues.append("reviewed_files_count != 3")
        if payload.get("expected_files_count") != 3:
            issues.append("expected_files_count != 3")
        if payload.get("unexpected_files_count") != 0:
            issues.append("unexpected_files_count != 0")
        if payload.get("missing_expected_files_count") != 0:
            issues.append("missing_expected_files_count != 0")
        if payload.get("total_data_bytes_observed", 0) > 20_000:
            issues.append("total_data_bytes_observed > 20000")
        if payload.get("preview_records_count", 0) > 5:
            issues.append("preview_records_count > 5")
        return {"safety_check_passed": not issues, "safety_issues": issues}
