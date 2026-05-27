from __future__ import annotations

from copy import deepcopy

from galapagos.research.feature_label_separability_v9_14_1 import CORRECTION_SCOPE, FINDINGS, SAFETY, SAFETY_FLAGS, SOURCE_VERSION, VERSION
from galapagos.research.feature_label_separability_v9_14_1_validation import (
    validate_hypotheses_payload_v9_14_1,
    validate_inventory_payload_v9_14_1,
    validate_manifest_payload_v9_14_1,
    validate_markdown_v9_14_1,
    validate_report_payload_v9_14_1,
)


def _inventory() -> list[dict]:
    sources = [
        "ohlcv",
        "public_trades_aggTrades",
        "order_book_l2",
        "funding_rates",
        "open_interest",
        "liquidations",
        "long_short_ratios",
        "multi_exchange_multi_venue",
        "on_chain",
        "macro_news_sentiment",
        "other_derivatives",
    ]
    result = []
    for source in sources:
        present = source in {"ohlcv", "public_trades_aggTrades", "funding_rates", "open_interest"}
        result.append(
            {
                "source_name": source,
                "present_in_repo": present,
                "used_in_validated_v9_chain": source in {"ohlcv", "public_trades_aggTrades"},
                "evidence_paths": [f"reports/{source}.json"] if present else [],
                "known_quality": "partial" if present else "not_available",
                "known_coverage": "coverage",
                "known_frequency": "frequency",
                "causality_feasibility": "good",
                "historical_availability": "medium",
                "leakage_risk": "low",
                "integration_complexity": "medium",
                "potential_value": "high",
                "recommended_priority": "priority_1_candidate" if source in {"funding_rates", "open_interest"} else "missing_or_unknown" if not present else "not_recommended_now",
                "notes": "notes",
            }
        )
    return result


def _hypotheses() -> list[dict]:
    return [
        {
            "id": f"H{index}",
            "hypothesis": "hypothesis",
            "status": "likely" if index in {2, 7, 11} else "possible",
            "evidence_for": ["for"],
            "evidence_against": ["against"],
            "confidence": "medium",
            "consequence_next_version": "consequence",
        }
        for index in range(1, 12)
    ]


def _valid_report() -> dict:
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "correction_scope": CORRECTION_SCOPE,
        "status": "PASS",
        "previous_v9_14_decision": "feature_first_before_more_labels",
        "corrected_decision": "data_extension_first_before_more_labels",
        "data_source_inventory": _inventory(),
        "hypothesis_ranking": _hypotheses(),
        "findings": dict(FINDINGS),
        "safety": dict(SAFETY),
        "safety_flags": dict(SAFETY_FLAGS),
    }


def test_validator_accepts_valid_report_v9_14_1() -> None:
    assert validate_report_payload_v9_14_1(_valid_report()) == []


def test_validator_rejects_missing_h11_v9_14_1() -> None:
    hypotheses = _hypotheses()[:-1]

    assert "V9.14.1 hypotheses H1-H11 must be complete" in validate_hypotheses_payload_v9_14_1(hypotheses)


def test_validator_rejects_present_source_without_evidence_v9_14_1() -> None:
    inventory = _inventory()
    inventory[3]["evidence_paths"] = []

    assert any("lacks evidence paths" in error for error in validate_inventory_payload_v9_14_1(inventory))


def test_validator_rejects_data_extension_without_priority_source_v9_14_1() -> None:
    inventory = _inventory()
    for item in inventory:
        if item["recommended_priority"] == "priority_1_candidate":
            item["present_in_repo"] = False
            item["evidence_paths"] = []

    assert any("requires a present priority_1" in error for error in validate_inventory_payload_v9_14_1(inventory, "data_extension_first_before_more_labels"))


def test_validator_rejects_previous_decision_changed_v9_14_1() -> None:
    report = _valid_report()
    report["previous_v9_14_decision"] = "inconclusive_need_manual_review"

    assert "V9.14.1 must preserve previous V9.14 decision" in validate_report_payload_v9_14_1(report)


def test_validator_rejects_strategy_validated_true_v9_14_1() -> None:
    report = _valid_report()
    report["findings"]["strategy_validated"] = True

    assert "V9.14.1 findings mismatch" in validate_report_payload_v9_14_1(report)


def test_validator_rejects_walk_forward_flag_false_v9_14_1() -> None:
    report = _valid_report()
    report["safety_flags"]["no_walk_forward"] = False

    assert "V9.14.1 safety flag mismatch: no_walk_forward" in validate_report_payload_v9_14_1(report)


def test_validator_rejects_sidecar_field_v9_14_1() -> None:
    report = _valid_report()
    manifest = deepcopy(report)
    manifest.update(
        {
            "version": VERSION,
            "source_version": SOURCE_VERSION,
            "correction_scope": CORRECTION_SCOPE,
            "status": "PASS",
            "corrected_decision": "data_extension_first_before_more_labels",
            "data_source_inventory_count": len(report["data_source_inventory"]),
            "hypotheses_count": len(report["hypothesis_ranking"]),
            "sidecar_json": "forbidden",
        }
    )

    assert "V9.14.1 manifest must not contain sidecar or ZIP hash fields" in validate_manifest_payload_v9_14_1(manifest, report)


def test_validator_rejects_markdown_forbidden_claim_v9_14_1() -> None:
    text = "Aucun backtest. Aucun trading. Aucun ordre. Aucune strategie. Aucun signal actionnable. Aucun walk-forward. H11 data-extension. tradable edge confirmed"

    assert any("forbidden claim" in error for error in validate_markdown_v9_14_1(text))


def test_validator_rejects_markdown_trading_metric_v9_14_1() -> None:
    text = "Aucun backtest. Aucun trading. Aucun ordre. Aucune strategie. Aucun signal actionnable. Aucun walk-forward. H11 data-extension. Sharpe."

    assert any("forbidden metric term" in error for error in validate_markdown_v9_14_1(text))
