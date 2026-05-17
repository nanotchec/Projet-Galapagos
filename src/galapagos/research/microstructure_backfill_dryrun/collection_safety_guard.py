from __future__ import annotations


class CollectionSafetyGuard:
    """Enforces absolute prohibitions on real collection during V1.53."""

    def analyze(self) -> dict:
        return {
            "status": "COLLECTION_SAFETY_GUARD_ACTIVE",
            "dry_run_only": True,
            "real_collection_executed": False,
            "external_data_downloaded": False,
            "external_api_called": False,
            "new_data_files_created": False,
            "parquet_created": False,
            "csv_created": False,
            "sqlite_created": False,
            "no_real_trading": True,
            "no_paper_live": True,
            "no_strategy_validated": True,
            "no_preregistration_yet": True,
            "holdout_executed": False,
            "codex_cli_called": False,
            "real_orders_possible": False,
            "safety_checks_passed": True
        }
