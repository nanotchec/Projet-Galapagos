from __future__ import annotations


class LabelPolicyDesigner:
    def design(self) -> dict[str, object]:
        return {
            "version": "V1.96",
            "label_policy_created": True,
            "label_horizon_policy_defined": True,
            "label_available_after_horizon_policy_defined": True,
            "label_not_available_at_decision_ts_policy_defined": True,
            "labels_for_training_forbidden_in_v1_96": True,
            "labels_joined_to_features_forbidden_in_v1_96": True,
            "predictions_forbidden": True,
            "model_training_forbidden": True,
            "trading_forbidden": True,
            "future_label_materialization_requires_v1_96_approval": True,
            "future_label_materialization_allowed_root": "data/research/label_preview/v1_97/",
            "future_label_materialization_max_files": 4,
            "future_label_materialization_max_bytes": 50000,
            "future_label_materialization_allowed_extensions": [".json"],
            "future_label_materialization_no_network": True,
            "future_label_materialization_no_ml": True,
            "future_label_materialization_no_trading": True,
            "allowed_future_label_kinds": [
                "horizon_direction_preview",
                "horizon_return_bucket_preview",
                "horizon_volatility_bucket_preview",
            ],
            "forbidden_v1_96_actions": [
                "physical_label_write",
                "target_write",
                "prediction_write",
                "training_join",
                "model_training",
                "trading",
            ],
        }

