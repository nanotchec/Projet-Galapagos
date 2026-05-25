from __future__ import annotations

import importlib.util
import sys
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts/validate_research_decision_gate_v8_1.py"
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("validate_research_decision_gate_v8_1", SCRIPT_PATH)
assert SPEC is not None
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

_find_forbidden_artifacts = MODULE._find_forbidden_artifacts
_validate_markdown_claims = MODULE._validate_markdown_claims
validate_research_decision_gate_v8_1 = MODULE.validate_research_decision_gate_v8_1
validate_research_decision_payload_v8_1 = MODULE.validate_research_decision_payload_v8_1


def test_validator_v8_1_accepts_valid_research_decision_gate() -> None:
    result = validate_research_decision_gate_v8_1(ROOT)

    assert result["passed"] is True
    assert result["errors"] == []


def test_validator_v8_1_rejects_non_research_decision_type() -> None:
    payload = deepcopy(validate_research_decision_gate_v8_1(ROOT)["report"])
    payload["decision_gate_type"] = "trading_approval"

    errors = validate_research_decision_payload_v8_1(payload)

    assert _contains(errors, "decision_gate_type must be research_only")


def test_validator_v8_1_rejects_missing_ohlcv_trades_90d_assessment() -> None:
    payload = deepcopy(validate_research_decision_gate_v8_1(ROOT)["report"])
    payload["ohlcv_trades_90d_assessment"] = {}

    errors = validate_research_decision_payload_v8_1(payload)

    assert _contains(errors, "ohlcv_trades_90d_assessment must be present")


def test_validator_v8_1_rejects_safety_flag_true() -> None:
    payload = deepcopy(validate_research_decision_gate_v8_1(ROOT)["report"])
    payload["safety"]["trading_enabled"] = True

    errors = validate_research_decision_payload_v8_1(payload)

    assert _contains(errors, "safety flag must be false: trading_enabled")


def test_validator_v8_1_rejects_claim_flag_true() -> None:
    payload = deepcopy(validate_research_decision_gate_v8_1(ROOT)["report"])
    payload["claims"]["ohlcv_trades_validated_for_trading"] = True

    errors = validate_research_decision_payload_v8_1(payload)

    assert _contains(errors, "claim flag must be false: ohlcv_trades_validated_for_trading")


def test_validator_v8_1_rejects_empty_roadmap() -> None:
    payload = deepcopy(validate_research_decision_gate_v8_1(ROOT)["report"])
    payload["roadmap"] = []

    errors = validate_research_decision_payload_v8_1(payload)

    assert _contains(errors, "roadmap must be non-empty")


def test_validator_v8_1_rejects_forbidden_markdown_claim(tmp_path: Path) -> None:
    markdown = tmp_path / "report.md"
    markdown.write_text("Tradable edge confirmed.\n", encoding="utf-8")

    errors = _validate_markdown_claims(markdown, "V8.1 Markdown report")

    assert _contains(errors, "forbidden claim")


def test_validator_v8_1_rejects_forbidden_artifact(tmp_path: Path) -> None:
    forbidden = tmp_path / "data/research/v8_1/backtests/backtest.json"
    forbidden.parent.mkdir(parents=True)
    forbidden.write_text("{}", encoding="utf-8")

    errors = _find_forbidden_artifacts(tmp_path)

    assert _contains(errors, "Forbidden V8.1 artifact detected")


def _contains(errors: list[str], needle: str) -> bool:
    return any(needle in error for error in errors)
