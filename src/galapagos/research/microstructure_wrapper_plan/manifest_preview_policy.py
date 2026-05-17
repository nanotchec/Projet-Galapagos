from typing import Any

def define_manifest_preview_policy(previous_state: dict[str, Any]) -> dict[str, Any]:
    """
    Defines the policy for generating manifest previews without data files.
    """
    return {
        "status": "MICROSTRUCTURE_MANIFEST_PREVIEW_POLICY_DEFINED",
        "manifest_preview_policy_defined": True,
        "manifest_data_file_created": False,
        "manifest_preview_generated": False, # Will be generated in future phase
        "expected_preview_fields": [
            "source",
            "symbol",
            "timeframe",
            "request_window",
            "expected_rows_preview",
            "checksum_policy",
            "available_ts_policy",
            "ingest_ts_policy",
            "no_lookahead_confirmation"
        ]
    }
