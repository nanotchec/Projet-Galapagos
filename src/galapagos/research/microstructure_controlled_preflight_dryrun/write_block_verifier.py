from pathlib import Path

def verify_write_block():
    data_dir = Path("data")
    forbidden_exts = [".parquet", ".csv", ".sqlite", ".db", ".jsonl"]
    
    issues = []
    if data_dir.exists():
        for p in data_dir.rglob("*"):
            if p.is_file() and p.suffix in forbidden_exts:
                issues.append(f"Forbidden data file found: {p}")
                
    status = "PASSED" if not issues else "FAILED"
    return {
        "status": status,
        "write_block_status": "WRITE_BLOCK_PASSED" if status == "PASSED" else "WRITE_BLOCK_FAILED",
        "forbidden_files_detected": issues,
        "data_directory_writes": False if status == "PASSED" else True,
        "allowed_reporting_only": True
    }
