from __future__ import annotations

from typing import Any

EXPECTED_APPROVAL_PHRASE = "J'approuve V1.92 mini research dataset seed ultra-borné, sans réseau, sans dataset complet, sans ML, sans trading."
EXPECTED_FUTURE_SCOPE = "mini_research_dataset_seed_ultra_bounded_no_network_no_full_dataset_no_ml_no_trading"


def evaluate_approval_phrase(phrase: str) -> dict[str, Any]:
    match = phrase == EXPECTED_APPROVAL_PHRASE
    return {
        "approval_phrase_expected_exact": EXPECTED_APPROVAL_PHRASE,
        "approval_phrase_provided": phrase,
        "approval_phrase_match": match,
        "human_approval_granted": match,
        "v1_92_authorized": match,
        "authorized_future_version": "V1.92" if match else None,
        "authorized_future_scope": EXPECTED_FUTURE_SCOPE if match else None,
        "v1_92_execution_attempted": False,
    }
