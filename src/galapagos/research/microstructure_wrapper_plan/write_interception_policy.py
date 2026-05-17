from typing import Any

def define_write_interception_policy(previous_state: dict[str, Any]) -> dict[str, Any]:
    """
    Defines strict write interception rules.
    """
    return {
        "status": "MICROSTRUCTURE_WRITE_INTERCEPTION_POLICY_DEFINED",
        "write_interception_defined": True,
        "no_data_directory_writes": True,
        "allowed_writes": [
            "reports/*.json",
            "reports/*.md"
        ],
        "forbidden_writes": [
            "data/",
            "parquet",
            "csv",
            "sqlite",
            "db",
            "jsonl",
            "real manifest data"
        ],
        "parquet_created": False,
        "csv_created": False,
        "sqlite_created": False,
        "new_data_files_created": False,
        "manifest_data_file_created": False,
    }
