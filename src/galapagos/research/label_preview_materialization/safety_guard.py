from __future__ import annotations

from typing import Any


class LabelPreviewSafetyGuard:
    REQUIRED_FALSE = [
        "physical_targets_created",
        "targets_created_in_data",
        "predictions_created",
        "feature_label_join_created",
        "training_dataset_created",
        "model_training_executed",
        "ml_signal_validation_executed",
        "network_executed",
        "trading_allowed",
        "real_orders_possible",
    ]

    def check(self, payload: dict[str, Any]) -> dict[str, Any]:
        issues = [field for field in self.REQUIRED_FALSE if payload.get(field) is not False]
        return {"version": "V1.97", "safety_check_passed": not issues, "safety_issues": issues}

