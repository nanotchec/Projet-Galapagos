import json
import subprocess
import sys

import pytest
import yaml
from pydantic import ValidationError

from galapagos.agent.decision_parser import (
    attempt_json_repair,
    parse_decision_response_with_metadata,
)
from galapagos.agent.decision_postprocessor import postprocess_decision_for_risk
from galapagos.agent.decision_prompt import build_llm_decision_prompt
from galapagos.agent.decision_schema import AgentDecision
from galapagos.agent.llm_providers import CodexCLIProvider, MockLLMProvider, OpenAICodexProvider
from galapagos.agent.llm_safety import apply_llm_safety
from galapagos.agent.subprocess_safety import (
    SubprocessSafetyError,
    require_read_only_sandbox,
    run_codex_exec_safely,
)
from galapagos.reports.codex_cli_report import analyze_codex_cli_decisions
from galapagos.reports.parser_fallback_report import analyze_parser_fallbacks


def decision_payload(**overrides) -> dict:
    payload = {
        "decision": "NO_TRADE",
        "profile": "galapagos_30m",
        "asset": "BTC/USD",
        "strategy": "no_trade",
        "confidence": 0.5,
        "reasoning_summary": "No edge.",
        "horizon": "30m",
        "reference_entry_price": None,
        "stop_loss": None,
        "take_profit": None,
        "risk_fraction": 0.0,
        "max_duration_minutes": 0,
        "invalidation_conditions": [],
        "critical_data_used": [],
    }
    payload.update(overrides)
    return payload


def test_openai_codex_provider_config_status() -> None:
    provider = OpenAICodexProvider(
        {
            "provider_name": "openai-codex",
            "auth_mode": "chatgpt_codex",
            "strict_json": True,
            "max_retries": 2,
        }
    )
    status = provider.status
    assert status["provider"] == "openai-codex"
    assert not status["available"]
    assert status["allow_network_calls"] is False
    assert "ChatGPT/Codex runtime bridge exposed to Python" in status["missing"]
    with pytest.raises(RuntimeError, match="network calls are disabled"):
        provider.complete([], {})


def test_llm_config_targets_gpt55_low() -> None:
    with open("configs/llm.yaml", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    assert config["model"] == "gpt-5.5"
    assert config["reasoning_effort"] == "low"
    assert config["allow_network_calls"] is False
    assert config["provider"] == "codex_cli"
    assert config["allow_codex_cli_calls"] is False
    assert config["codex_cli"]["sandbox"] == "read-only"


def test_prompt_contains_anti_overtrading_rules() -> None:
    prompt = build_llm_decision_prompt({"portfolio": {"has_open_position": True}})
    assert prompt.startswith("CRITICAL OUTPUT RULE")
    assert "NO_TRADE if edge is unclear" in prompt
    assert "Never invent unavailable data" in prompt
    assert "Do not call tools" in prompt
    assert "read-only sandboxed" in prompt
    assert "Conservative mode rules" in prompt


def test_balanced_prompt_mentions_derivatives_do_not_auto_block() -> None:
    prompt = build_llm_decision_prompt(
        {"portfolio": {"has_open_position": False}},
        prompt_mode="balanced",
    )
    assert "Balanced mode rules" in prompt
    assert "Derivatives unavailable must not automatically block a trade" in prompt
    assert "setup_quality" in prompt
    assert "why_not_no_trade" in prompt


def test_setup_review_prompt_contains_review_rules() -> None:
    prompt = build_llm_decision_prompt(
        {"candidate_setup": {"exists": True}},
        prompt_mode="setup_review",
    )
    assert "Setup review mode rules" in prompt
    assert "Review only candidate_setup" in prompt
    assert "Do not search for another trade" in prompt
    assert "Position state rules" in prompt
    assert "You may propose LONG or SHORT only when portfolio.has_open_position is false" in prompt
    assert "Required critical_data_used for active decisions" in prompt
    assert "['price', 'volatility', 'trend_short', 'trend_long', 'candidate_setup']" in prompt
    assert "Cost awareness" in prompt
    assert "STRICT ENUM RULES" in prompt
    assert '"poor", "acceptable", "good", "excellent"' in prompt
    assert '"medium", "moderate", "unclear"' in prompt
    assert '"setup_quality_score": 0.20' in prompt


def test_codex_cli_provider_refuses_without_allow_flag() -> None:
    provider = CodexCLIProvider({"allow_codex_cli_calls": False})
    result = provider.generate('{"test": true}')
    assert result.error == "codex_cli provider is configured but allow_codex_cli_calls=false."
    assert result.raw_response == ""


def test_codex_cli_provider_enforces_prompt_size() -> None:
    provider = CodexCLIProvider(
        {
            "allow_codex_cli_calls": True,
            "codex_cli": {"max_prompt_chars": 4, "sandbox": "read-only"},
        }
    )
    result = provider.generate("too long")
    assert "exceeds max_prompt_chars" in str(result.error)


def test_codex_cli_provider_requires_read_only_sandbox() -> None:
    with pytest.raises(SubprocessSafetyError):
        require_read_only_sandbox("workspace-write")
    provider = CodexCLIProvider(
        {
            "allow_codex_cli_calls": True,
            "codex_cli": {"sandbox": "workspace-write"},
        }
    )
    result = provider.generate("{}")
    assert "sandbox must be read-only" in str(result.error)


def test_codex_cli_provider_mocked_subprocess_parses_json(monkeypatch) -> None:
    from galapagos.agent import llm_providers
    from galapagos.agent.subprocess_safety import SafeSubprocessResult

    captured = {}

    def fake_which(executable: str) -> str:
        return f"/usr/bin/{executable}"

    def fake_run(command, *, timeout_seconds, output_last_message=True):
        captured["command"] = command
        captured["timeout_seconds"] = timeout_seconds
        return SafeSubprocessResult(
            exit_code=0,
            duration_seconds=0.1,
            stdout='{"ok": true}',
            stderr="",
            output_file_text='{"ok": true, "provider": "codex_cli"}',
            output_file_used="/tmp/fake.json",
        )

    monkeypatch.setattr(llm_providers.shutil, "which", fake_which)
    monkeypatch.setattr(llm_providers, "run_codex_exec_safely", fake_run)
    provider = CodexCLIProvider(
        {
            "allow_codex_cli_calls": True,
            "codex_cli": {"sandbox": "read-only", "timeout_seconds": 7},
        }
    )
    result = provider.generate("prompt")
    assert json.loads(result.raw_response)["provider"] == "codex_cli"
    assert captured["timeout_seconds"] == 7
    assert captured["command"][0:4] == ["codex", "exec", "-m", "gpt-5.5"]
    assert "--sandbox" in captured["command"]
    assert "read-only" in captured["command"]


def test_safe_subprocess_measures_duration() -> None:
    result = run_codex_exec_safely(
        [sys.executable, "-c", "print('ok')"],
        timeout_seconds=5,
        output_last_message=False,
    )
    assert result.exit_code == 0
    assert result.duration_seconds > 0
    assert result.stdout.strip() == "ok"


def test_safe_subprocess_timeout_duration() -> None:
    result = run_codex_exec_safely(
        [sys.executable, "-c", "import time; time.sleep(2)"],
        timeout_seconds=1,
        output_last_message=False,
    )
    assert result.exit_code is None
    assert result.duration_seconds >= 1
    assert "timed out" in str(result.error)


def test_codex_cli_report_includes_duration_stats() -> None:
    analysis = analyze_codex_cli_decisions(
        {
            "decisions": [
                {
                    "provider_name": "codex_cli",
                    "provider_duration_seconds": 1.0,
                    "parser_validity": "valid_schema",
                    "decision_validity": "valid_schema",
                    "decision": "NO_TRADE",
                    "risk_approved": True,
                    "raw_response": json.dumps(
                        decision_payload(
                            reasoning_summary="Edge unclear and derivatives unavailable."
                        )
                    ),
                },
                {
                    "provider_name": "codex_cli",
                    "provider_duration_seconds": 3.0,
                    "parser_validity": "valid_schema",
                    "decision_validity": "valid_schema",
                    "decision": "NO_TRADE",
                    "risk_approved": True,
                    "raw_response": json.dumps(decision_payload()),
                },
            ],
            "metrics": {},
        },
        {"decisions": [{"decision": "NO_TRADE"}, {"decision": "LONG"}], "metrics": {}},
    )
    assert analysis["min_duration_seconds"] == 1.0
    assert analysis["average_duration_seconds"] == 2.0
    assert analysis["max_duration_seconds"] == 3.0
    assert analysis["no_trade_rate"] == 1.0
    assert analysis["decision_agreement_vs_offline_conservative"]["matches"] == 1


def test_codex_cli_provider_missing_output_is_clean_error(monkeypatch) -> None:
    from galapagos.agent import llm_providers
    from galapagos.agent.subprocess_safety import SafeSubprocessResult

    monkeypatch.setattr(llm_providers.shutil, "which", lambda _: "/usr/bin/codex")
    monkeypatch.setattr(
        llm_providers,
        "run_codex_exec_safely",
        lambda *args, **kwargs: SafeSubprocessResult(
            exit_code=0,
            duration_seconds=0.1,
            stdout="",
            stderr="",
            output_file_text="",
            output_file_used="/tmp/fake.json",
        ),
    )
    provider = CodexCLIProvider({"allow_codex_cli_calls": True})
    result = provider.generate("prompt")
    assert "did not produce" in str(result.error)


def test_llm_safety_unavailable_and_suspicious_confidence() -> None:
    decision = AgentDecision(
        decision="LONG",
        profile="galapagos_30m",
        asset="BTC/USD",
        strategy="momentum",
        confidence=0.99,
        reasoning_summary="Uses unavailable funding.",
        horizon="30m",
        reference_entry_price=100,
        stop_loss=99,
        take_profit=102,
        risk_fraction=0.002,
        max_duration_minutes=240,
        invalidation_conditions=[],
        critical_data_used=["funding"],
    )
    result = apply_llm_safety(
        decision,
        profile={"name": "galapagos_30m", "symbol": "BTC/USD", "timeframe": "30m"},
        risk_config={"max_risk_per_trade": 0.005},
        unavailable_features=["funding"],
    )
    assert result.fallback_applied is True
    assert "suspicious_confidence" in result.flags
    assert result.decision.decision == "NO_TRADE"


def test_llm_safety_balanced_acceptable_limits_risk() -> None:
    decision = AgentDecision(
        decision="LONG",
        profile="galapagos_4h",
        asset="BTC/USD",
        strategy="momentum",
        confidence=0.7,
        reasoning_summary="Technical trend and momentum compensate for missing derivatives.",
        horizon="4h",
        reference_entry_price=100,
        stop_loss=99,
        take_profit=102,
        risk_fraction=0.004,
        max_duration_minutes=240,
        invalidation_conditions=[],
        critical_data_used=["price"],
        setup_quality="acceptable",
        why_not_no_trade="Technical signals align.",
    )
    result = apply_llm_safety(
        decision,
        profile={"name": "galapagos_4h", "symbol": "BTC/USD", "timeframe": "4h"},
        risk_config={"max_risk_per_trade": 0.005},
        unavailable_features=["funding", "open_interest", "basis", "liquidations"],
        prompt_mode="balanced",
    )
    assert result.fallback_applied is True
    assert "balanced_acceptable_setup_risk_too_high" in result.flags


def test_postprocessor_fallback_long_without_price() -> None:
    decision = AgentDecision.model_validate(
        decision_payload(
            decision="LONG",
            strategy="momentum",
            reference_entry_price=100.0,
            stop_loss=99.0,
            take_profit=102.0,
            risk_fraction=0.001,
            max_duration_minutes=240,
            critical_data_used=["volatility"],
        )
    )
    result = postprocess_decision_for_risk(
        decision,
        decision_context={"available_critical_data": {"price": True, "volatility": True}},
        config={"decision_postprocessing": {"missing_required_policy": "fallback_no_trade"}},
    )
    assert result.action == "fallback_no_trade"
    assert result.decision.decision == "NO_TRADE"
    assert result.missing_required == ["price"]


def test_postprocessor_fallback_long_without_volatility() -> None:
    decision = AgentDecision.model_validate(
        decision_payload(
            decision="LONG",
            strategy="momentum",
            reference_entry_price=100.0,
            stop_loss=99.0,
            take_profit=102.0,
            risk_fraction=0.001,
            max_duration_minutes=240,
            critical_data_used=["price"],
        )
    )
    result = postprocess_decision_for_risk(
        decision,
        decision_context={"available_critical_data": {"price": True, "volatility": True}},
        config={"decision_postprocessing": {"missing_required_policy": "fallback_no_trade"}},
    )
    assert result.action == "fallback_no_trade"
    assert result.decision.decision == "NO_TRADE"
    assert result.missing_required == ["volatility"]


def test_postprocessor_allows_long_with_price_and_volatility() -> None:
    decision = AgentDecision.model_validate(
        decision_payload(
            decision="LONG",
            strategy="momentum",
            reference_entry_price=100.0,
            stop_loss=99.0,
            take_profit=102.0,
            risk_fraction=0.001,
            max_duration_minutes=240,
            critical_data_used=["price", "volatility"],
        )
    )
    result = postprocess_decision_for_risk(
        decision,
        decision_context={"available_critical_data": {"price": True, "volatility": True}},
        config={"decision_postprocessing": {"missing_required_policy": "fallback_no_trade"}},
    )
    assert result.action == "unchanged_active"
    assert result.decision.decision == "LONG"


def test_postprocessor_overrides_same_direction_entry_to_hold() -> None:
    decision = AgentDecision.model_validate(
        decision_payload(
            decision="LONG",
            strategy="momentum",
            reference_entry_price=100.0,
            stop_loss=99.0,
            take_profit=102.0,
            risk_fraction=0.001,
            max_duration_minutes=240,
            critical_data_used=["price", "volatility"],
        )
    )
    result = postprocess_decision_for_risk(
        decision,
        decision_context={
            "portfolio": {"has_open_position": True, "position_side": "LONG"},
            "available_critical_data": {"price": True, "volatility": True},
        },
        config={"decision_postprocessing": {"missing_required_policy": "fallback_no_trade"}},
    )
    assert result.action == "stateful_override_hold"
    assert result.stateful_override is True
    assert result.decision.decision == "HOLD"


def test_postprocessor_overrides_opposite_entry_without_invalidation_to_no_trade() -> None:
    decision = AgentDecision.model_validate(
        decision_payload(
            decision="SHORT",
            strategy="momentum",
            reasoning_summary="Opposite setup but no explicit exit signal.",
            reference_entry_price=100.0,
            stop_loss=101.0,
            take_profit=98.0,
            risk_fraction=0.001,
            max_duration_minutes=240,
            critical_data_used=["price", "volatility"],
        )
    )
    result = postprocess_decision_for_risk(
        decision,
        decision_context={
            "portfolio": {"has_open_position": True, "position_side": "LONG"},
            "available_critical_data": {"price": True, "volatility": True},
        },
        config={"decision_postprocessing": {"missing_required_policy": "fallback_no_trade"}},
    )
    assert result.action == "stateful_override_no_trade"
    assert result.decision.decision == "NO_TRADE"


def test_parser_accepts_json_block_and_text() -> None:
    raw = f"Analyse:\n```json\n{json.dumps(decision_payload())}\n```"
    result = parse_decision_response_with_metadata(raw, "galapagos_30m", "BTC/USD", "30m")
    assert result.validity == "valid_schema"
    assert result.decision.decision == "NO_TRADE"
    assert result.parser_repair_applied is True


def test_parser_extracts_json_surrounded_by_text() -> None:
    raw = "prefix " + json.dumps(
        decision_payload(
            decision="HOLD",
            strategy="risk_reduction",
            confidence=0.6,
            reasoning_summary="Wait.",
        )
    ) + " suffix"
    result = parse_decision_response_with_metadata(raw, "galapagos_30m", "BTC/USD", "30m")
    assert result.validity == "valid_schema"
    assert result.decision.decision == "HOLD"
    assert result.parser_repair_applied is True


def test_attempt_json_repair_markdown_and_text() -> None:
    payload = json.dumps(decision_payload())
    assert attempt_json_repair(f"```json\n{payload}\n```") == payload
    assert attempt_json_repair(f"prefix {payload} suffix") == payload


def test_attempt_json_repair_refuses_truncated_json() -> None:
    assert attempt_json_repair('{"decision":"NO_TRADE"') is None


@pytest.mark.parametrize(
    "raw",
    [
        "{bad json",
        '{"decision":"BUY"}',
        '{"decision":"NO_TRADE","profile":"x"}',
        json.dumps(decision_payload(confidence=2, reasoning_summary="Bad.")),
    ],
)
def test_parser_fallbacks_to_no_trade(raw: str) -> None:
    result = parse_decision_response_with_metadata(raw, "galapagos_30m", "BTC/USD", "30m")
    assert result.validity == "parser_fallback"
    assert result.decision.decision == "NO_TRADE"


@pytest.mark.parametrize("score", [0.0, 0.5, 1.0])
def test_setup_quality_score_accepts_valid_range(score: float) -> None:
    decision = AgentDecision.model_validate(decision_payload(setup_quality_score=score))
    assert decision.setup_quality_score == score


@pytest.mark.parametrize("score", [-0.1, 1.1])
def test_setup_quality_score_rejects_invalid_range(score: float) -> None:
    with pytest.raises(ValidationError):
        AgentDecision.model_validate(decision_payload(setup_quality_score=score))


def test_parser_diagnostic_identifies_invalid_enum() -> None:
    raw = json.dumps(decision_payload(setup_quality="medium"))
    result = parse_decision_response_with_metadata(raw, "galapagos_30m", "BTC/USD", "30m")
    assert result.validity == "parser_fallback"
    assert result.enum_violations == [
        {
            "field_name": "setup_quality",
            "invalid_value": "medium",
            "allowed_values": ["poor", "acceptable", "good", "excellent"],
        }
    ]


def test_parser_report_generated(tmp_path) -> None:
    report = tmp_path / "setup.json"
    report.write_text(
        json.dumps(
            {
                "reviews": [
                    {
                        "candidate": {"candidate_id": "c1"},
                        "parser_validity": "parser_fallback",
                        "raw_response": "prefix {bad",
                        "parser_error": "Unclosed JSON object",
                        "enum_violations": [],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    analysis = analyze_parser_fallbacks(report)
    assert analysis["parser_fallback_count"] == 1
    assert analysis["fallbacks"][0]["candidate_id"] == "c1"


def test_parser_report_lists_enum_violations(tmp_path) -> None:
    report = tmp_path / "setup.json"
    report.write_text(
        json.dumps(
            {
                "reviews": [
                    {
                        "candidate": {"candidate_id": "c2"},
                        "parser_validity": "parser_fallback",
                        "raw_response": json.dumps(decision_payload(setup_quality="medium")),
                        "raw_response_preview": '{"setup_quality":"medium"}',
                        "parser_error": "string_pattern_mismatch",
                        "enum_violations": [
                            {
                                "field_name": "setup_quality",
                                "invalid_value": "medium",
                                "allowed_values": ["poor", "acceptable", "good", "excellent"],
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    analysis = analyze_parser_fallbacks(report)
    assert analysis["enum_violations_count"] == 1
    assert analysis["top_invalid_enum_values"] == {"setup_quality=medium": 1}
    assert analysis["enum_violations"][0]["candidate_id"] == "c2"


@pytest.mark.parametrize("decision", ["NO_TRADE", "LONG", "SHORT", "CLOSE", "HOLD"])
def test_mock_provider_supports_all_decisions(decision: str) -> None:
    raw = MockLLMProvider(decision).complete(
        [],
        {
            "profile": {"name": "galapagos_30m", "symbol": "BTC/USD", "timeframe": "30m"},
            "market": {"last_close": 100.0},
        },
    )
    assert json.loads(raw)["decision"] == decision


def test_llm_provider_mock_script_runs() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/test_llm_provider.py", "--provider", "mock"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert '"provider": "mock"' in completed.stdout


def test_llm_provider_codex_cli_script_refuses_without_allow() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/test_llm_provider.py", "--provider", "codex_cli"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "codex_cli calls require --allow-codex-cli" in completed.stdout


def test_sample_backtest_codex_cli_refuses_without_allow() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_llm_sample_backtest.py",
            "--profile",
            "4h",
            "--bars",
            "5",
            "--provider",
            "codex_cli",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "codex_cli sample requires --allow-codex-cli" in completed.stdout


def test_codex_prompt_mode_comparison_script_runs_with_mock() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_codex_prompt_mode_comparison.py",
            "--provider",
            "mock",
            "--profile",
            "4h",
            "--bars",
            "2",
            "--modes",
            "conservative,balanced",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "codex_prompt_mode_comparison_v1_8C_2" in completed.stdout


def test_codex_setup_review_script_runs_with_mock() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_codex_setup_review.py",
            "--provider",
            "mock",
            "--profile",
            "4h",
            "--max-candidates",
            "2",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "codex_setup_review_v1_8C_9" in completed.stdout


def test_sample_backtest_mock_script_runs() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_llm_sample_backtest.py",
            "--profile",
            "4h",
            "--bars",
            "10",
            "--provider",
            "mock",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert '"provider": "mock"' in completed.stdout
