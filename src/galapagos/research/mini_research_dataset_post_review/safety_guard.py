from __future__ import annotations

from typing import Any


class MiniResearchDatasetPostReviewSafetyGuard:
    def check(self, payload: dict[str, Any]) -> dict[str, Any]:
        issues: list[str] = []
        
        expected_true = [
            "post_seed_review_executed",
            "review_only",
            "reports_only",
            "no_new_data_directory_writes",
            "seed_checksums_verified",
            "schema_validation_passed",
            "available_ts_policy_present",
            "decision_ts_policy_present",
            "no_lookahead_policy_present",
            "no_strategy_validated",
            "no_paper_live",
            "no_real_trading"
        ]
        for field in expected_true:
            if payload.get(field) is not True:
                issues.append(f"{field} != true")

        expected_false = [
            "dataset_seed_created",
            "new_dataset_seed_created",
            "data_directory_write_attempted",
            "new_data_files_created",
            "existing_seed_files_modified",
            "leakage_detected",
            "lookahead_detected",
            "network_executed",
            "trading_allowed",
            "ml_signal_validation_executed"
        ]
        for field in expected_false:
            if payload.get(field) is not False:
                issues.append(f"{field} != false")

        if payload.get("reviewed_files_count", 0) != 5:
             issues.append("reviewed_files_count != 5")
        
        if payload.get("total_data_bytes_observed", 99999) > 50000:
             issues.append("total_data_bytes_observed > 50000")

        if payload.get("preview_records_count", 99) > 10:
             issues.append("preview_records_count > 10")

        return {
            "safety_check_passed": not issues,
            "safety_issues": issues
        }
