def define_write_gate(version: str) -> dict:
    return {
        "version": version, "current_version": version,
        "no_data_directory_writes": True,
        "new_data_files_created": False,
        "allowed_writes": ["reports/research/*.json", "reports/research/*.md", "reports/*.json", "reports/*.md"],
        "forbidden_writes": ["data/*", "*.parquet", "*.csv", "*.sqlite", "*.db", "*.jsonl"],
        "write_protection_level": "REPORTING_ONLY",
        "policy_status": "LOCKED"
    }
