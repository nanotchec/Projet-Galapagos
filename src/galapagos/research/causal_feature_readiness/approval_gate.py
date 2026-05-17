from __future__ import annotations


EXPECTED_APPROVAL_PHRASE = (
    "J'approuve V1.95 feature preview materialization ultra-bornée, sans réseau, "
    "sans labels, sans targets, sans ML, sans trading."
)
AUTHORIZED_SCOPE = "feature_preview_materialization_ultra_bounded_no_network_no_labels_no_targets_no_ml_no_trading"


class CausalFeatureApprovalGate:
    def __init__(self, expected_phrase: str = EXPECTED_APPROVAL_PHRASE) -> None:
        self.expected_phrase = expected_phrase

    def evaluate(self, provided_phrase: str) -> dict[str, object]:
        match = provided_phrase == self.expected_phrase
        return {
            "approval_phrase_expected_exact": self.expected_phrase,
            "approval_phrase_provided": provided_phrase,
            "approval_phrase_match": match,
            "human_approval_granted": match,
            "v1_95_authorized": match,
            "authorized_future_version": "V1.95" if match else None,
            "authorized_future_scope": AUTHORIZED_SCOPE if match else None,
            "v1_95_execution_attempted": False,
        }
