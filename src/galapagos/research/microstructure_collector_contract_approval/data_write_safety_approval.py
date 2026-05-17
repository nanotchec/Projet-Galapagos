from __future__ import annotations

class DataWriteSafetyVerifier:
    def __init__(self, metrics: dict[str, Any]):
        self.metrics = metrics

    def verify(self) -> dict[str, Any]:
        no_writes = self.metrics.get("no_data_directory_writes", False)
        parquet = self.metrics.get("parquet_created", True)
        csv = self.metrics.get("csv_created", True)
        sqlite = self.metrics.get("sqlite_created", True)
        files_created = self.metrics.get("new_data_files_created", True)
        
        passed = no_writes and not parquet and not csv and not sqlite and not files_created
        
        return {
            "status": "PASSED" if passed else "FAILED",
            "no_data_directory_writes": no_writes,
            "parquet_created": parquet,
            "csv_created": csv,
            "sqlite_created": sqlite,
            "new_data_files_created": files_created,
            "data_write_safety_approved": passed
        }
