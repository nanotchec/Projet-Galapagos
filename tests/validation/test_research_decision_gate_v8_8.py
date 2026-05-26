from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_research_decision_gate_v8_8 import (
    DECISION_JSON,
    validate_research_decision_gate_v8_8,
    validate_research_decision_markdown_text_v8_8,
    validate_research_decision_payload_v8_8,
)


def test_decision_gate_v8_8_is_research_only() -> None:
    payload = _load_decision()

    assert payload["decision_gate_type"] == "research_only"
    assert validate_research_decision_payload_v8_8(payload) == []


def test_decision_gate_v8_8_has_feature_refinement_recommendation() -> None:
    payload = _load_decision()

    assert payload["recommended_next_step"].startswith("A.")
    assert "features OHLCV + trades" in payload["recommended_next_step"]
    assert payload["secondary_next_step"].startswith("B.")
    assert payload["roadmap"][0].startswith("V8.9")


def test_decision_gate_v8_8_preserves_label_shuffle_warning_count() -> None:
    payload = _load_decision()

    assert payload["label_shuffle_assessment"]["no_clear_edge_vs_shuffled_labels_count"] == 18
    assert payload["label_shuffle_assessment"]["falsification_clean"] is False
    assert payload["label_shuffle_assessment"]["by_timeframe"] == {"1m": 12, "1h": 6}


def test_decision_gate_v8_8_claims_false() -> None:
    payload = _load_decision()

    assert set(payload["claims"]) == {
        "strategy_validated",
        "model_validated_for_trading",
        "walk_forward_validated_for_trading",
        "profitability_claimed",
        "real_trading_allowed",
    }
    assert all(value is False for value in payload["claims"].values())


def test_decision_gate_v8_8_no_backtest_recommendation() -> None:
    result = validate_research_decision_gate_v8_8(ROOT)

    assert result["passed"] is True
    assert result["errors"] == []
    assert result["report"]["safety"]["backtest_enabled"] is False
    assert result["report"]["baseline_assessment"]["backtest_recommended"] is False
    assert not result["report"]["recommended_next_step"].startswith("E.")


def test_decision_gate_v8_8_rejects_claim_true() -> None:
    payload = deepcopy(_load_decision())
    payload["claims"]["walk_forward_validated_for_trading"] = True

    errors = validate_research_decision_payload_v8_8(payload)

    assert any("claims mismatch" in error for error in errors)


def test_decision_gate_v8_8_rejects_backtest_primary_recommendation() -> None:
    payload = deepcopy(_load_decision())
    payload["recommended_next_step"] = "E. Preparer un backtest research tres borne."

    errors = validate_research_decision_payload_v8_8(payload)

    assert any("must not recommend a backtest" in error for error in errors)


def test_decision_gate_v8_8_rejects_forbidden_markdown_claim() -> None:
    text = (
        "# Test\n\n"
        "V8.7 est une validation walk-forward offline stricte, pas un backtest.\n"
        "Un backtest research n'est pas justifie maintenant.\n"
        "Pas de trading. Pas de paper live. Pas d'ordre.\n"
        "tradable edge confirmed.\n"
    )

    errors = validate_research_decision_markdown_text_v8_8(text, "markdown fixture")

    assert any("tradable edge confirmed" in error for error in errors)


def _load_decision() -> dict[str, Any]:
    return json.loads((ROOT / DECISION_JSON).read_text(encoding="utf-8"))
