from pathlib import Path
from typing import Any, Dict

class NoDataWriteGuard:
    def __init__(self, root: Path):
        self.root = root

    def check_for_data_files(self) -> Dict[str, Any]:
        data_dir = self.root / "data"
        if not data_dir.exists():
            return {
                "new_data_files_created": False,
                "no_data_directory_writes": True,
                "parquet_created": False,
                "csv_created": False,
                "sqlite_created": False,
                "jsonl_created": False,
                "db_created": False
            }
            
        # Check for any common data formats
        parquet_files = list(data_dir.glob("**/*.parquet"))
        csv_files = list(data_dir.glob("**/*.csv"))
        sqlite_files = list(data_dir.glob("**/*.sqlite")) + list(data_dir.glob("**/*.db"))
        jsonl_files = list(data_dir.glob("**/*.jsonl"))
        
        has_new = len(parquet_files) > 0 or len(csv_files) > 0 or len(sqlite_files) > 0 or len(jsonl_files) > 0
        
        return {
            "new_data_files_created": has_new,
            "no_data_directory_writes": not has_new,
            "parquet_created": len(parquet_files) > 0,
            "csv_created": len(csv_files) > 0,
            "sqlite_created": len(sqlite_files) > 0,
            "jsonl_created": len(jsonl_files) > 0,
            "db_created": len(sqlite_files) > 0
        }
