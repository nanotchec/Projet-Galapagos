from __future__ import annotations


class ExtensionGateSafetyGuard:
    """Checks V1.86 remains a reports-only approval gate."""

    EXPECTED = {
        "approval_gate_only": True,
        "reports_only": True,
        "v1_87_execution_attempted": False,
        "materialization_executed": False,
        "new_materialization_executed": False,
        "data_contract_actual_write_executed": False,
        "scope_drift_detected": False,
        "data_directory_writes_allowed": False,
        "data_directory_write_attempted": False,
        "new_data_files_created": False,
        "existing_data_files_modified": False,
        "no_new_data_directory_writes": True,
        "dataset_created": False,
        "research_dataset_updated": False,
        "network_executed": False,
        "new_network_requests_executed": False,
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
    }

    def check(self, payload: dict) -> dict:
        issues = [
            f"{field}={payload.get(field)!r}, expected {expected!r}"
            for field, expected in self.EXPECTED.items()
            if payload.get(field) is not expected
        ]
        if payload.get("request_retry_count") != 0:
            issues.append("request_retry_count != 0")
        if payload.get("physical_files_created_count") != 0:
            issues.append("physical_files_created_count != 0")
        return {"safety_check_passed": not issues, "safety_issues": issues}
