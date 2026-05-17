from __future__ import annotations

from dataclasses import dataclass

EXPECTED_APPROVAL_PHRASE = (
    "J'approuve V1.84 tiny data contract materialization ultra-bornée, "
    "sans réseau, sans dataset complet, sans ML, sans trading."
)
AUTHORIZED_SCOPE = (
    "tiny_data_contract_materialization_ultra_bounded_no_network_"
    "no_full_dataset_no_ml_no_trading"
)


@dataclass(frozen=True)
class ApprovalGate:
    expected_phrase: str = EXPECTED_APPROVAL_PHRASE

    def evaluate(self, provided_phrase: str) -> dict:
        phrase = provided_phrase or ""
        match = phrase == self.expected_phrase
        return {
            "approval_phrase_expected_exact": self.expected_phrase,
            "approval_phrase_provided": phrase,
            "approval_phrase_match": match,
            "human_approval_granted": match,
            "v1_84_authorized": match,
            "authorized_future_version": "V1.84" if match else None,
            "authorized_future_scope": AUTHORIZED_SCOPE if match else None,
        }
