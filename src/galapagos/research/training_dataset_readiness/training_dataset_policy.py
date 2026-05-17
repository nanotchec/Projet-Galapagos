from __future__ import annotations


class TrainingDatasetPolicyDesigner:
    def design(self) -> dict[str, object]:
        return {
            "version": "V1.98.2",
            "training_dataset_policy_created": True,
            "future_training_dataset_materialization_requires_v1_98_approval": True,
            "future_training_dataset_allowed_root": "data/research/training_dataset_preview/v1_99/",
            "future_training_dataset_max_files": 5,
            "future_training_dataset_max_bytes": 75000,
            "future_training_dataset_allowed_extensions": [".json"],
            "future_training_dataset_no_network": True,
            "future_training_dataset_no_ml": True,
            "future_training_dataset_no_backtest": True,
            "future_training_dataset_no_trading": True,
            "purge_policy_defined": True,
            "embargo_policy_defined": True,
            "temporal_split_policy_defined": True,
            "no_random_shuffle_policy_defined": True,
            "label_availability_policy_defined": True,
            "policy_notes": [
                "Tout futur dataset d'entrainement doit rester preview ultra-bornee.",
                "Les labels ne sont utilisables qu'apres leur horizon et jamais au decision_ts.",
                "Les splits doivent etre temporels avec purge et embargo theoriques.",
            ],
        }
