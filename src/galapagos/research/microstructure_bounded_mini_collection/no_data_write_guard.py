from pathlib import Path
from typing import Any, Dict

class NoDataWriteGuard:
    def __init__(self, root: Path):
        self.root = root

    def check_for_data_files(self) -> Dict[str, Any]:
        data_dir = self.root / "data"
        if not data_dir.exists():
            return {"no_data_directory_writes": True, "files_found": []}
            
        # We check for new parquet, csv, sqlite, jsonl, db files
        forbidden_exts = {".parquet", ".csv", ".sqlite", ".jsonl", ".db"}
        found = []
        for p in data_dir.rglob("*"):
            if p.suffix in forbidden_exts:
                found.append(str(p.relative_to(self.root)))
                
        return {
            "no_data_directory_writes": len(found) == 0,
            "new_data_files_created": len(found) > 0,
            "files_found": found,
            "parquet_created": any(f.endswith(".parquet") for f in found),
            "csv_created": any(f.endswith(".csv") for f in found),
            "sqlite_created": any(f.endswith(".sqlite") for f in found),
            "jsonl_created": any(f.endswith(".jsonl") for f in found),
            "db_created": any(f.endswith(".db") for f in found)
        }
