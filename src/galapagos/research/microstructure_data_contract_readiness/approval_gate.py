from typing import Any, Dict

class ApprovalGate:
    def get_status(self) -> Dict[str, Any]:
        return {
            "approval_gate_version": "V1.80",
            "future_version_requiring_approval": "V1.81",
            "approval_required_for": "tiny_data_contract_materialization_dryrun_reports_only_no_data_write",
            "human_approval_phrase_expected_exact": "J'approuve V1.81 dry-run data contract reports-only, sans écriture data, sans dataset, sans trading.",
            "human_approval_phrase_provided": "",
            "human_approval_granted": False,
            "v1_81_authorized": False
        }
