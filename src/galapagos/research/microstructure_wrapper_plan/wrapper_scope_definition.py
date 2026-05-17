from typing import Any

def define_wrapper_scope(previous_state: dict[str, Any]) -> dict[str, Any]:
    """
    Defines the strict scope of the wrapper. 
    Explicitly states that this phase (V1.63) is ONLY a planning phase.
    """
    return {
        "status": "MICROSTRUCTURE_WRAPPER_SCOPE_DEFINED",
        "wrapper_plan_only": True,
        "wrapper_executed": False,
        "controlled_local_preflight_executed": False,
        "real_preflight_executed": False,
        "network_enabled": False,
        "network_disabled": True,
        "network_disabled_by_default": True,
        "future_network_activation_requires_separate_approval": True,
        "real_collection_approved": False,
        "real_collection_approval_status": "NOT_APPROVED",
        "real_collection_executed": False,
        "human_review_required_before_collection": True,
        "dry_run_only": True,
        "local_fixture_only": True,
        "fixture_only": True,
        "synthetic_or_minimal_sample": True,
        "not_for_research_results": True,
        "simulated_requests_allowed": True,
        "requests_executed_count": 0,
        "external_api_called": False,
        "external_data_downloaded": False,
        "new_data_files_created": False,
        "no_data_directory_writes": True,
        "parquet_created": False,
        "csv_created": False,
        "sqlite_created": False,
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "codex_cli_called": False,
        "real_orders_possible": False,
        "manifest_data_file_created": False,
    }
