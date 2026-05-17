from __future__ import annotations

from typing import Any


class MiniResearchDatasetSeedSafetyGuard:
    def check(self, payload: dict[str, Any]) -> dict[str, Any]:
        issues: list[str] = []
        expected_true = [
            "approval_source_verified",
            "human_approval_granted",
            "approval_phrase_match",
            "v1_92_authorized",
            "dataset_seed_created",
            "mini_research_dataset_seed_only",
            "data_directory_writes_allowed",
            "data_write_approved",
            "data_directory_write_attempted",
            "new_data_files_created",
            "dataset_seed_actual_write_executed",
            "anti_leakage_plan_applied",
            "available_ts_policy_applied",
            "event_ts_policy_applied",
            "decision_ts_policy_applied",
            "feature_available_ts_lte_decision_ts_rule_applied",
            "no_lookahead_policy_applied",
            "provenance_policy_applied",
            "manifest_checksum_policy_applied",
            "schema_validation_policy_applied",
            "physical_seed_semantic_scan_executed",
            "no_strategy_validated",
            "no_paper_live",
            "no_real_trading",
        ]
        expected_false = [
            "full_dataset_created",
            "scope_drift_detected",
            "reports_only",
            "no_data_directory_writes",
            "unapproved_data_write_detected",
            "existing_v1_84_files_modified",
            "existing_v1_87_files_modified",
            "existing_v1_90_files_modified",
            "parquet_created",
            "csv_created",
            "sqlite_created",
            "jsonl_created",
            "db_created",
            "dataset_created",
            "research_dataset_updated",
            "labels_created",
            "targets_created",
            "predictions_created",
            "ml_signal_validation_executed",
            "feature_generation_executed",
            "model_training_executed",
            "leakage_detected",
            "lookahead_detected",
            "future_information_fields_detected",
            "forbidden_target_like_fields_detected",
            "forbidden_seed_terms_detected",
            "target_like_fields_detected",
            "label_like_fields_detected",
            "prediction_like_fields_detected",
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
        ]
        for field in expected_true:
            if payload.get(field) is not True:
                issues.append(f"{field} != true")
        for field in expected_false:
            if payload.get(field) is not False:
                issues.append(f"{field} != false")
        if payload.get("request_retry_count") != 0:
            issues.append("request_retry_count != 0")
        if payload.get("allowed_data_write_root") != "data/research/dataset_seed/v1_92/":
            issues.append("allowed_data_write_root mismatch")
        if payload.get("total_new_data_files_created") != 5:
            issues.append("total_new_data_files_created != 5")
        if payload.get("created_files_count") != 5:
            issues.append("created_files_count != 5")
        if payload.get("total_data_bytes_written", 999_999) > 50_000:
            issues.append("total_data_bytes_written > 50000")
        if payload.get("preview_records_count", 99) > 10:
            issues.append("preview_records_count > 10")
        if payload.get("forbidden_seed_terms_count") != 0:
            issues.append("forbidden_seed_terms_count != 0")
        if payload.get("forbidden_seed_term_occurrences") != []:
            issues.append("forbidden_seed_term_occurrences != []")
        return {"safety_check_passed": not issues, "safety_issues": issues}
