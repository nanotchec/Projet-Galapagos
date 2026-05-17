from __future__ import annotations

from typing import Any

EXPECTED_FALSE = [
    "full_dataset_created",
    "scope_drift_detected",
    "reports_only",
    "network_executed",
    "new_network_requests_executed",
    "pagination_used",
    "authenticated_request_allowed",
    "secrets_used",
    "unapproved_data_write_detected",
    "parquet_created",
    "csv_created",
    "sqlite_created",
    "jsonl_created",
    "db_created",
    "dataset_created",
    "research_dataset_updated",
    "dataset_materialization_approved",
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

EXPECTED_TRUE = [
    "human_approval_granted",
    "approval_phrase_match",
    "approval_source_verified",
    "v1_84_authorized",
    "materialization_executed",
    "tiny_materialization_only",
    "data_directory_writes_allowed",
    "data_write_approved",
    "data_directory_write_attempted",
    "data_contract_actual_write_executed",
    "new_data_files_created",
    "manifest_json_created",
    "schema_snapshot_json_created",
    "preview_records_json_created",
    "no_strategy_validated",
    "no_paper_live",
    "no_real_trading",
]


class MaterializationSafetyGuard:
    """Checks V1.84 remains ultra-bounded and disconnected from network, ML and trading."""

    def check(self, payload: dict[str, Any]) -> dict[str, Any]:
        issues: list[str] = []
        for field in EXPECTED_TRUE:
            if payload.get(field) is not True:
                issues.append(f"{field} != true")
        for field in EXPECTED_FALSE:
            if payload.get(field) is not False:
                issues.append(f"{field} != false")
        if payload.get("no_data_directory_writes") is not False:
            issues.append("no_data_directory_writes != false")
        if payload.get("request_retry_count") != 0:
            issues.append("request_retry_count != 0")
        if payload.get("created_files_count", 0) > 3:
            issues.append("created_files_count > 3")
        if payload.get("total_data_files_created", 0) > 3:
            issues.append("total_data_files_created > 3")
        if payload.get("total_data_bytes_written", 0) > 20_000:
            issues.append("total_data_bytes_written > 20000")
        if payload.get("preview_records_count", 0) > 5:
            issues.append("preview_records_count > 5")
        return {
            "safety_check_passed": not issues,
            "safety_issues": issues,
        }
