from __future__ import annotations

import argparse
import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.agent.decision_context import build_decision_context
from galapagos.agent.decision_parser import parse_decision_response_with_metadata
from galapagos.agent.decision_prompt import build_llm_decision_prompt
from galapagos.agent.decision_validator import validate_decision_context
from galapagos.agent.llm_providers import CodexCLIProvider, MockLLMProvider, OpenAICodexProvider
from galapagos.utils.config_loader import load_yaml


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["mock", "openai-codex", "codex_cli"], required=True)
    parser.add_argument("--allow-network", action="store_true")
    parser.add_argument("--allow-codex-cli", action="store_true")
    parser.add_argument("--model")
    parser.add_argument("--reasoning-effort")
    parser.add_argument(
        "--prompt-mode",
        choices=["conservative", "balanced"],
        default="conservative",
    )
    args = parser.parse_args()
    config = load_yaml("configs/llm.yaml")
    if args.allow_network:
        config["allow_network_calls"] = True
    if args.model:
        config["model"] = args.model
    if args.reasoning_effort:
        config["reasoning_effort"] = args.reasoning_effort
        config.setdefault("codex_cli", {})["reasoning_effort"] = args.reasoning_effort
    if args.model:
        config.setdefault("codex_cli", {})["model"] = args.model
    if args.allow_codex_cli:
        config["allow_codex_cli_calls"] = True
    context = _minimal_context(config)
    prompt = build_llm_decision_prompt(context, prompt_mode=args.prompt_mode)
    output = {
        "safe_config": _safe_config(config),
        "prompt_chars": len(prompt),
        "errors": [],
    }
    try:
        if args.provider == "mock":
            provider = MockLLMProvider("NO_TRADE")
            raw = provider.complete([], {"profile": _profile(), "market": {"last_close": 100}})
            output["provider_status"] = provider.status
        elif args.provider == "openai-codex":
            provider = OpenAICodexProvider(config)
            output["provider_status"] = provider.diagnose()
            raw = provider.complete([{"role": "user", "content": prompt}], context.to_dict())
        else:
            provider = CodexCLIProvider(config)
            output["provider_status"] = provider.diagnose()
            if not args.allow_codex_cli:
                raise RuntimeError("codex_cli calls require --allow-codex-cli.")
            result = provider.generate(
                'Réponds uniquement avec ce JSON exact : {"ok": true, "provider": "codex_cli"}'
            )
            output["provider_result"] = {
                "provider_name": result.provider_name,
                "model": result.model,
                "reasoning_effort": result.reasoning_effort,
                "duration_seconds": result.duration_seconds,
                "exit_code": result.exit_code,
                "error": result.error,
                "available": result.available,
                "stdout_preview": result.stdout_preview,
                "stderr_preview": result.stderr_preview,
            }
            raw = result.raw_response
            if result.error:
                raise RuntimeError(result.error)
            minimal = json.loads(raw)
            output["minimal_json_parse_success"] = minimal == {
                "ok": True,
                "provider": "codex_cli",
            }
            print(json.dumps(output | {"raw_response": raw}, indent=2, ensure_ascii=False))
            return
        parsed = parse_decision_response_with_metadata(raw, "galapagos_4h", "BTC/USD", "4h")
        validation = validate_decision_context(
            parsed.decision,
            profile=_profile(),
            market={"last_close": 100.0},
            derivatives={"funding": {"status": "unavailable"}},
            config=config,
        )
        output.update(
            {
                "raw_response": raw,
                "parsed_decision": parsed.decision.model_dump(mode="json"),
                "decision_validity": validation.validity
                if validation.validity != "valid_schema"
                else parsed.validity,
            }
        )
    except Exception as exc:  # noqa: BLE001
        output["errors"].append(str(exc))
    print(json.dumps(output, indent=2, ensure_ascii=False))


def _minimal_context(config: dict):
    return build_decision_context(
        profile=_profile(),
        market={"last_close": 100.0, "last_high": 101, "last_low": 99, "last_volume": 10},
        indicators={"sma_20": 101, "sma_50": 100, "realized_volatility": 0.01, "market_regime": {}},
        derivatives={"funding": {"status": "unavailable"}},
        scenarios=[],
        portfolio={"current_position": None, "current_price": 100.0},
        risk_config=load_yaml("configs/risk.yaml"),
        decision_timestamp="2026-01-01T00:00:00+00:00",
        data_mode="diagnostic",
        run_id="diagnostic",
        ohlcv_window=[],
    )


def _profile() -> dict:
    return {
        "name": "galapagos_4h",
        "symbol": "BTC/USD",
        "timeframe": "4h",
        "paper_trading_only": True,
        "max_position_duration_minutes": 1440,
    }


def _safe_config(config: dict) -> dict:
    return {
        key: ("***" if "key" in key.lower() or "secret" in key.lower() else value)
        for key, value in config.items()
        if key != "context_validation"
    }


if __name__ == "__main__":
    main()
