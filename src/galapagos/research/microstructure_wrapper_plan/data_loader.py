import json
from pathlib import Path
from typing import Any


def load_previous_state(
    hardened_preflight_review_summary_path: str,
    hardened_preflight_review_consistency_path: str,
    hardened_preflight_next_phase_policy_path: str,
    hardened_preflight_recommendation_path: str,
    v1_62_1_recommendation_path: str,
    preflight_hardening_summary_path: str,
    preflight_dryrun_summary_path: str,
    preflight_plan_summary_path: str,
    adapter_fixture_summary_path: str,
    adapter_field_mapping_path: str,
    normalized_record_schema_path: str,
    source_adapter_contract_path: str,
    request_builder_path: str,
    canonical_summary_path: str,
) -> dict[str, Any]:
    """Loads previous states to ensure prerequisites are met."""
    
    def _load_json(path_str: str) -> dict[str, Any]:
        p = Path(path_str)
        if not p.exists():
            raise FileNotFoundError(f"Missing required input file: {p}")
        with open(p) as f:
            return json.load(f)

    return {
        "hardened_preflight_review_summary": _load_json(hardened_preflight_review_summary_path),
        "hardened_preflight_review_consistency": _load_json(hardened_preflight_review_consistency_path),
        "hardened_preflight_next_phase_policy": _load_json(hardened_preflight_next_phase_policy_path),
        "hardened_preflight_recommendation": _load_json(hardened_preflight_recommendation_path),
        "v1_62_1_recommendation": _load_json(v1_62_1_recommendation_path),
        "preflight_hardening_summary": _load_json(preflight_hardening_summary_path),
        "preflight_dryrun_summary": _load_json(preflight_dryrun_summary_path),
        "preflight_plan_summary": _load_json(preflight_plan_summary_path),
        "adapter_fixture_summary": _load_json(adapter_fixture_summary_path),
        "adapter_field_mapping": _load_json(adapter_field_mapping_path),
        "normalized_record_schema": _load_json(normalized_record_schema_path),
        "source_adapter_contract": _load_json(source_adapter_contract_path),
        "request_builder": _load_json(request_builder_path),
        "canonical_summary": _load_json(canonical_summary_path),
    }
