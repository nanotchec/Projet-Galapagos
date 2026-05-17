from __future__ import annotations


class ApprovalGateSafetyGuard:
    """Checks V1.83 remains a reports-only approval gate."""

    EXPECTED = {
        "v1_84_execution_attempted": False,
        "materialization_executed": False,
        "data_contract_actual_write_executed": False,
        "data_directory_write_attempted": False,
        "new_data_files_created": False,
        "no_data_directory_writes": True,
        "dataset_created": False,
        "network_executed": False,
        "trading_allowed": False,
        "real_orders_possible": False,
        "ml_signal_validation_executed": False,
        "approval_gate_only": True,
        "reports_only": True,
    }

    def check(self, payload: dict) -> dict:
        issues = [
            f"{field}={payload.get(field)!r}, expected {expected!r}"
            for field, expected in self.EXPECTED.items()
            if payload.get(field) is not expected
        ]
        return {
            "safety_check_passed": not issues,
            "safety_issues": issues,
        }
