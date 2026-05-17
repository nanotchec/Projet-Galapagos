from __future__ import annotations

from typing import Any

APPROVAL_PHRASE_EXPECTED = (
    "J'approuve V1.90 tiny data contract consolidation ultra-bornée, sans réseau, "
    "sans dataset complet, sans ML, sans trading."
)
AUTHORIZED_FUTURE_SCOPE = "tiny_data_contract_consolidation_ultra_bounded_no_network_no_full_dataset_no_ml_no_trading"


def evaluate_approval_phrase(approval_phrase: str) -> dict[str, Any]:
    phrase_match = approval_phrase == APPROVAL_PHRASE_EXPECTED
    return {
        "approval_phrase_expected_exact": APPROVAL_PHRASE_EXPECTED,
        "approval_phrase_provided": approval_phrase,
        "approval_phrase_match": phrase_match,
        "human_approval_granted": phrase_match,
        "v1_90_authorized": phrase_match,
        "authorized_future_version": "V1.90" if phrase_match else None,
        "authorized_future_scope": AUTHORIZED_FUTURE_SCOPE if phrase_match else None,
        "v1_90_execution_attempted": False,
    }
