from __future__ import annotations

from typing import Any


def design_dataset_seed() -> dict[str, Any]:
    return {
        "dataset_seed_design_created": True,
        "dataset_seed_plan_reports_only": True,
        "dataset_seed_plan_theoretical_paths_only": True,
        "future_dataset_seed_requires_v1_91_approval": True,
        "future_dataset_seed_allowed_root": "data/research/dataset_seed/v1_92/",
        "future_dataset_seed_max_files": 5,
        "future_dataset_seed_max_bytes": 50_000,
        "future_dataset_seed_allowed_extensions": [".json"],
        "future_dataset_seed_forbidden_extensions": [".parquet", ".csv", ".sqlite", ".jsonl", ".db"],
        "future_dataset_seed_no_network": True,
        "future_dataset_seed_no_ml": True,
        "future_dataset_seed_no_trading": True,
        "future_dataset_seed_no_full_dataset": True,
        "future_dataset_rows_preview_limit": 10,
        "target_files_theoretical": [
            "data/research/dataset_seed/v1_92/seed_manifest.json",
            "data/research/dataset_seed/v1_92/seed_schema.json",
            "data/research/dataset_seed/v1_92/seed_preview_records.json",
            "data/research/dataset_seed/v1_92/seed_provenance.json",
            "data/research/dataset_seed/v1_92/seed_quality_audit.json",
        ],
    }
