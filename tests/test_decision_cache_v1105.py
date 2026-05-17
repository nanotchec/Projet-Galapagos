from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from galapagos.agent.decision_cache import (
    DecisionCache,
    DecisionCacheEntry,
    build_decision_cache_key,
)


def test_cache_key_is_deterministic_and_sensitive_to_prompt_and_constraints() -> None:
    base = {
        "context_hash": "context",
        "prompt_hash": "prompt",
        "model": "gpt-5.5",
        "reasoning_effort": "low",
        "prompt_mode": "setup_review",
        "constraints_config_hash": "constraints",
    }
    assert build_decision_cache_key(**base).cache_key == build_decision_cache_key(**base).cache_key
    assert build_decision_cache_key(**base).cache_key != build_decision_cache_key(
        **{**base, "prompt_hash": "other"}
    ).cache_key
    assert build_decision_cache_key(**base).cache_key != build_decision_cache_key(
        **{**base, "constraints_config_hash": "other"}
    ).cache_key


def test_cache_write_hit_and_refresh(tmp_path: Path) -> None:
    key = build_decision_cache_key(
        context_hash="context",
        prompt_hash="prompt",
        model="gpt-5.5",
        reasoning_effort="low",
        prompt_mode="setup_review",
        constraints_config_hash="constraints",
    )
    cache = DecisionCache(tmp_path)
    entry = _entry(key.cache_key, reasoning="first")
    cache.put(key, entry)

    hit = cache.get(key)
    assert hit is not None
    assert hit.parsed_decision["reasoning_summary"] == "first"

    cache.refresh(key, _entry(key.cache_key, reasoning="second"))
    refreshed = cache.get(key)
    assert refreshed is not None
    assert refreshed.parsed_decision["reasoning_summary"] == "second"


def test_cache_miss_readonly_policy_is_detectable(tmp_path: Path) -> None:
    key = build_decision_cache_key(
        context_hash="missing",
        prompt_hash="prompt",
        model="gpt-5.5",
        reasoning_effort="low",
        prompt_mode="setup_review",
        constraints_config_hash="constraints",
    )
    assert DecisionCache(tmp_path).get(key) is None


def test_replay_script_blocks_holdout_by_default() -> None:
    module = _load_script("replay_cached_decisions")
    with pytest.raises(RuntimeError, match="Holdout cached replay is blocked"):
        module.replay_cached_decisions(
            config_path=Path("configs/evaluation/btc_4h_long_only_force_close_v1_10_1.yaml"),
            windows=["holdout"],
            use_decision_cache=True,
            cache_readonly=True,
            allow_holdout=False,
        )


def test_build_script_blocks_holdout_by_default() -> None:
    module = _load_script("build_decision_cache")
    with pytest.raises(RuntimeError, match="Holdout cache build is blocked"):
        module.build_decision_cache(
            config_path=Path("configs/evaluation/btc_4h_long_only_force_close_v1_10_1.yaml"),
            windows=["holdout"],
            allow_codex_cli=False,
            max_calls=20,
            dry_run=True,
            refresh_cache=False,
            allow_holdout=False,
        )


def _entry(cache_key: str, *, reasoning: str) -> DecisionCacheEntry:
    decision = {
        "decision": "NO_TRADE",
        "profile": "galapagos_4h",
        "asset": "BTC/USD",
        "strategy": "no_trade",
        "confidence": 0.0,
        "reasoning_summary": reasoning,
        "horizon": "4h",
        "reference_entry_price": None,
        "stop_loss": None,
        "take_profit": None,
        "risk_fraction": 0.0,
        "max_duration_minutes": 0,
        "invalidation_conditions": [],
        "critical_data_used": [],
        "setup_quality": "poor",
        "setup_quality_score": 0.0,
        "why_not_no_trade": None,
    }
    return DecisionCacheEntry(
        cache_key=cache_key,
        context_hash="context",
        prompt_hash="prompt",
        model="gpt-5.5",
        reasoning_effort="low",
        prompt_mode="setup_review",
        constraints_config_hash="constraints",
        created_at_utc="2026-05-03T00:00:00+00:00",
        provider_name="codex_cli",
        raw_response="{}",
        parsed_decision=decision,
        decision_validity="valid_schema",
        parser_repair_applied=False,
        postprocessing_warnings=[],
        safety_warnings=[],
        duration_seconds=1.0,
        codex_exit_code=0,
        stdout_preview="",
        stderr_preview="",
    )


def _load_script(name: str):
    path = Path("scripts") / f"{name}.py"
    sys.path.insert(0, str(Path("scripts").resolve()))
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module
