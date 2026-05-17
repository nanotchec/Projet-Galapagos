from __future__ import annotations

from typing import Any


class LabelReadinessSafetyGuard:
    REQUIRED_FALSE = [
        "physical_labels_created",
        "physical_targets_created",
        "labels_created_in_data",
        "targets_created_in_data",
        "predictions_created",
        "model_training_executed",
        "ml_signal_validation_executed",
        "data_directory_write_attempted",
        "new_data_files_created",
        "network_executed",
        "trading_allowed",
        "real_orders_possible",
        "v1_97_execution_attempted",
    ]

    def check(self, payload: dict[str, Any]) -> dict[str, Any]:
        issues = [field for field in self.REQUIRED_FALSE if payload.get(field) is not False]
        return {
            "version": "V1.96",
            "safety_check_passed": not issues,
            "safety_issues": issues,
            "reports_only": payload.get("reports_only"),
            "no_real_trading": payload.get("no_real_trading"),
            "real_orders_possible": payload.get("real_orders_possible"),
        }

