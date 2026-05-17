from __future__ import annotations

from typing import Any


class ConsolidationSafetyGuard:
    """Checks V1.90 stays within the approved tiny consolidation scope."""

    def check(self, payload: dict[str, Any]) -> dict[str, Any]:
        issues: list[str] = []
        expected_true = [
            "approval_source_verified",
            "human_approval_granted",
            "approval_phrase_match",
            "v1_90_authorized",
            "consolidation_executed",
            "tiny_consolidation_only",
            "data_directory_writes_allowed",
            "data_write_approved",
            "data_directory_write_attempted",
            "consolidation_actual_write_executed",
            "new_data_files_created",
            "consolidated_manifest_json_created",
            "consolidated_schema_snapshot_json_created",
            "consolidated_quality_summary_json_created",
            "no_strategy_validated",
            "no_paper_live",
            "no_real_trading",
        ]
        expected_false = [
            "full_dataset_created",
            "scope_drift_detected",
            "reports_only",
            "network_executed",
            "new_network_requests_executed",
            "pagination_used",
            "authenticated_request_allowed",
            "secrets_used",
            "unapproved_data_write_detected",
            "existing_v1_84_files_modified",
            "existing_v1_87_files_modified",
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
        for field in expected_true:
            if payload.get(field) is not True:
                issues.append(f"{field} != true")
        for field in expected_false:
            if payload.get(field) is not False:
                issues.append(f"{field} != false")
        if payload.get("created_files_count", 99) > 3:
            issues.append("created_files_count > 3")
        if payload.get("total_new_data_files_created", 99) > 3:
            issues.append("total_new_data_files_created > 3")
        if payload.get("total_data_bytes_written", 99_999) > 25_000:
            issues.append("total_data_bytes_written > 25000")
        if payload.get("request_retry_count") != 0:
            issues.append("request_retry_count != 0")
        return {"safety_check_passed": not issues, "safety_issues": issues}
