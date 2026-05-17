from __future__ import annotations


class BackfillDryRunInputGuard:
    """Validates the input reports from V1.52 are ready for dry-run."""

    def validate(self, enrichment_summary: dict) -> tuple[str, dict]:
        flags = {
            "evidence_classification_aligned": False,
            "final_verdict_aligned": False,
            "data_contract_ready": False,
            "validation_acceptance_criteria_present": False,
            "no_real_trading": enrichment_summary.get("no_real_trading", False),
            "no_paper_live": enrichment_summary.get("no_paper_live", False),
            "external_data_downloaded": enrichment_summary.get("external_data_downloaded", True),
            "real_orders_possible": enrichment_summary.get("real_orders_possible", True),
        }

        expected_verdict = "MICROSTRUCTURE_ENRICHMENT_SPEC_READY"
        expected_classification = "INFRASTRUCTURE_ONLY"

        if enrichment_summary.get("final_verdict") == expected_verdict:
            flags["final_verdict_aligned"] = True
        
        if enrichment_summary.get("evidence_classification") == expected_classification:
            flags["evidence_classification_aligned"] = True

        if enrichment_summary.get("data_contract_ready") is True:
            flags["data_contract_ready"] = True
            
        if enrichment_summary.get("validation_acceptance_criteria"):
            flags["validation_acceptance_criteria_present"] = True

        all_passed = (
            flags["final_verdict_aligned"]
            and flags["evidence_classification_aligned"]
            and flags["data_contract_ready"]
            and flags["validation_acceptance_criteria_present"]
            and flags["no_real_trading"]
            and flags["no_paper_live"]
            and not flags["external_data_downloaded"]
            and not flags["real_orders_possible"]
        )

        status = "INPUT_VALID_FOR_DRY_RUN" if all_passed else "INPUT_REJECTED"
        return status, flags
