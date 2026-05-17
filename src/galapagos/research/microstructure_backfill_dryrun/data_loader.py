from __future__ import annotations
import json
from pathlib import Path


class BackfillDryRunDataLoader:
    """Loads infrastructure specs from V1.52 and earlier phases."""
    
    def __init__(
        self,
        enrichment_summary_path: str,
        required_field_spec_path: str,
        source_candidate_policy_path: str,
        causal_availability_spec_path: str,
        backfill_plan_path: str,
        validation_criteria_path: str,
        data_contract_path: str,
        quality_mask_summary_path: str,
        canonical_summary_path: str,
    ):
        self.paths = {
            "enrichment_summary": Path(enrichment_summary_path),
            "required_field_spec": Path(required_field_spec_path),
            "source_candidate_policy": Path(source_candidate_policy_path),
            "causal_availability_spec": Path(causal_availability_spec_path),
            "backfill_plan": Path(backfill_plan_path),
            "validation_criteria": Path(validation_criteria_path),
            "data_contract": Path(data_contract_path),
            "quality_mask_summary": Path(quality_mask_summary_path),
            "canonical_summary": Path(canonical_summary_path),
        }

    def load_report(self, key: str) -> dict:
        path = self.paths[key]
        if not path.exists():
            raise FileNotFoundError(f"Missing required report: {path}")
        with open(path) as f:
            return json.load(f)
