from __future__ import annotations

from dataclasses import dataclass

APPROVAL_PHRASE = "J'approuve V1.99 training dataset preview materialization ultra-bornée, sans réseau, sans ML, sans backtest, sans trading."
AUTHORIZED_SCOPE = "training_dataset_preview_materialization_ultra_bounded_no_network_no_ml_no_backtest_no_trading"


@dataclass(frozen=True)
class TrainingDatasetApprovalGate:
    expected_phrase: str = APPROVAL_PHRASE

    def evaluate(self, provided_phrase: str) -> dict[str, object]:
        matched = provided_phrase == self.expected_phrase
        return {
            "approval_phrase_expected_exact": self.expected_phrase,
            "approval_phrase_provided": provided_phrase,
            "approval_phrase_match": matched,
            "human_approval_granted": matched,
            "v1_99_authorized": matched,
            "authorized_future_version": "V1.99" if matched else None,
            "authorized_future_scope": AUTHORIZED_SCOPE if matched else None,
            "v1_99_execution_attempted": False,
        }
