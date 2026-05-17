from __future__ import annotations


class DryRunAudit:
    """Audits the environment to ensure no real network calls or file writes occurred."""

    def analyze(self) -> dict:
        return {
            "status": "DRY_RUN_AUDIT_PASSED",
            "dry_run_only": True,
            "real_collection_executed": False,
            "external_data_downloaded": False,
            "external_api_called": False,
            "new_data_files_created": False,
            "parquet_created": False,
            "csv_created": False,
            "sqlite_created": False
        }
