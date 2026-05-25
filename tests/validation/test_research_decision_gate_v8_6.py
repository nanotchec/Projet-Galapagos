from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_research_decision_gate_v8_6 import (
    validate_research_decision_gate_v8_6,
    validate_research_decision_payload_v8_6,
)
from galapagos.ml.ohlcv_trades_1y_robustness import DECISION_GATE_JSON_PATH_V8_6


def test_decision_gate_v8_6_is_research_only() -> None:
    payload = _load_decision()

    assert payload["decision_gate_type"] == "research_only"
    assert validate_research_decision_payload_v8_6(payload) == []


def test_decision_gate_v8_6_has_recommendation() -> None:
    payload = _load_decision()

    assert payload["recommended_next_step"].strip()
    assert payload["secondary_next_step"].strip()
    assert payload["roadmap"]


def test_decision_gate_v8_6_claims_false() -> None:
    payload = _load_decision()

    assert all(value is False for value in payload["claims"].values())


def test_decision_gate_v8_6_no_backtest_claim() -> None:
    result = validate_research_decision_gate_v8_6(ROOT)

    assert result["passed"] is True
    assert result["errors"] == []
    assert result["report"]["safety"]["backtest_enabled"] is False
    assert result["report"]["claims"]["profitability_claimed"] is False


def test_decision_gate_v8_6_rejects_claim_true() -> None:
    payload = deepcopy(_load_decision())
    payload["claims"]["strategy_validated"] = True

    errors = validate_research_decision_payload_v8_6(payload)

    assert any("claims mismatch" in error for error in errors)


def _load_decision() -> dict[str, Any]:
    return json.loads((ROOT / DECISION_GATE_JSON_PATH_V8_6).read_text(encoding="utf-8"))
