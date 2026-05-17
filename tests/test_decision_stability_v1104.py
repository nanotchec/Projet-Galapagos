from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from galapagos.analysis.decision_stability import (
    analyze_decision_stability,
    stability_verdict,
)

_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_codex_stability_analysis.py"
sys.path.insert(0, str(_SCRIPT_PATH.parent))
_SPEC = importlib.util.spec_from_file_location("run_codex_stability_analysis", _SCRIPT_PATH)
assert _SPEC and _SPEC.loader
_SCRIPT = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_SCRIPT)
run_stability_analysis = _SCRIPT.run_stability_analysis


def test_decision_agreement_and_flip_count() -> None:
    result = analyze_decision_stability(
        [
            {"index": 1, "windows": {"calibration": _report(["LONG", "NO_TRADE"])}},
            {"index": 2, "windows": {"calibration": _report(["NO_TRADE", "NO_TRADE"])}},
        ]
    )

    metrics = result["windows"]["calibration"]
    assert metrics["candidate_count"] == 2
    assert metrics["exact_decision_match_rate"] == 0.5
    assert metrics["long_no_trade_flip_count"] == 1


def test_pnl_variance_and_verdict() -> None:
    result = analyze_decision_stability(
        [
            {"index": 1, "windows": {"calibration": _report(["LONG"], pnl=10)}},
            {"index": 2, "windows": {"calibration": _report(["NO_TRADE"], pnl=-10)}},
        ]
    )

    assert result["windows"]["calibration"]["pnl_variance"]["std"] == 10.0
    assert result["verdict"] == "HIGHLY_UNSTABLE"
    assert stability_verdict({"exact_decision_match_rate": 0.9}) == "STABLE"


_STABILITY_CONFIG_YAML = """
version: V1.10.4
evaluation_name: test_stability
profile: galapagos_4h
asset: BTC/USD
timeframe: 4h
evaluation:
  stability_repetitions: 2
  windows: [calibration]
  holdout_enabled: false
windows:
  calibration:
    label: calibration
    max_candidates: 1
  validation_1:
    label: validation_1
    max_candidates: 1
  validation_2:
    label: validation_2
    max_candidates: 1
  holdout:
    label: holdout
    max_candidates: 1
"""


def test_stability_dry_run_does_not_call_codex(tmp_path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text(_STABILITY_CONFIG_YAML, encoding="utf-8")
    result = run_stability_analysis(
        config_path=config,
        repetitions=2,
        windows="calibration",
        max_calls=2,
        allow_codex_cli=False,
        dry_run=True,
    )

    assert result["dry_run"] is True
    assert result["planned_calls"] == 2
    assert result["holdout_executed"] is False
    assert result["status"] == "dry_run_completed"
    assert result["data_required_for_real_run"] is True
    assert isinstance(result["data_available"], bool)


def test_stability_real_run_requires_data(tmp_path, monkeypatch) -> None:
    """A real (non-dry) run must fail cleanly when no OHLCV data is cached."""
    config = tmp_path / "config.yaml"
    config.write_text(_STABILITY_CONFIG_YAML, encoding="utf-8")
    monkeypatch.setattr(
        _SCRIPT,
        "_find_longest_cached_ohlcv",
        lambda symbol, timeframe: None,
    )
    import pytest as _pytest

    with _pytest.raises(RuntimeError, match="No cached OHLCV data found"):
        run_stability_analysis(
            config_path=config,
            repetitions=2,
            windows="calibration",
            max_calls=60,
            allow_codex_cli=True,
            dry_run=False,
        )


def _report(decisions: list[str], pnl: float = 0.0) -> dict:
    return {
        "window_label": "calibration",
        "final_equity_pnl": pnl,
        "ledger_trade_count": sum(1 for decision in decisions if decision == "LONG"),
        "decision_distribution": {
            decision: decisions.count(decision) for decision in set(decisions)
        },
        "reviews": [
            {
                "candidate": {
                    "context_index": index,
                    "baseline_policy": "state_aware_momentum",
                    "baseline_decision": "LONG",
                    "current_price": 100 + index,
                },
                "decision": decision,
                "raw_response": (
                    f'{{"decision":"{decision}","setup_quality":"acceptable",'
                    '"confidence":0.6,"risk_fraction":0.003}'
                ),
            }
            for index, decision in enumerate(decisions)
        ],
    }
