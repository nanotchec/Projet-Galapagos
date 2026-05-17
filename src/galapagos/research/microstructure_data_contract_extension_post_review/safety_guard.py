from __future__ import annotations

from typing import Any


EXPECTED_TRUE = [
    "post_extension_review_executed",
    "review_only",
    "reports_only",
    "no_new_data_directory_writes",
    "v1_87_extension_manifest_json_valid",
    "v1_87_extension_quality_summary_json_valid",
    "v1_87_manifest_matches_physical_files",
    "v1_84_hashes_match_expected",
    "v1_87_hashes_match_expected",
    "no_strategy_validated",
    "no_paper_live",
    "no_real_trading",
]

EXPECTED_FALSE = [
    "extension_materialization_executed",
    "new_extension_materialization_executed",
    "materialization_executed",
    "data_contract_actual_write_executed",
    "scope_drift_detected",
    "data_directory_writes_allowed",
    "data_directory_write_attempted",
    "new_data_files_created",
    "existing_data_files_modified",
    "existing_v1_84_files_modified",
    "existing_v1_87_files_modified",
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


class ExtensionPostReviewSafetyGuard:
    """Checks V1.88 remains a reports-only review with no data writes."""

    def check(self, payload: dict[str, Any]) -> dict[str, Any]:
        issues: list[str] = []
        for field in EXPECTED_TRUE:
            if payload.get(field) is not True:
                issues.append(f"{field} != true")
        for field in EXPECTED_FALSE:
            if payload.get(field) is not False:
                issues.append(f"{field} != false")
        expected_counts = {
            "reviewed_v1_84_files_count": 3,
            "reviewed_v1_87_files_count": 2,
            "expected_v1_84_files_count": 3,
            "expected_v1_87_files_count": 2,
            "unexpected_v1_84_files_count": 0,
            "unexpected_v1_87_files_count": 0,
            "missing_v1_84_files_count": 0,
            "missing_v1_87_files_count": 0,
            "request_retry_count": 0,
        }
        for field, expected in expected_counts.items():
            if payload.get(field) != expected:
                issues.append(f"{field} != {expected}")
        if payload.get("total_v1_87_data_bytes_observed", 0) > 15_000:
            issues.append("total_v1_87_data_bytes_observed > 15000")
        return {"safety_check_passed": not issues, "safety_issues": issues}
