from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.agent.llm_providers import CodexCLIProvider
from galapagos.backtest.historical_data import find_latest_cached_ohlcv
from galapagos.backtest.replay_engine import ReplayEngine
from galapagos.reports.codex_cli_report import write_codex_cli_sample_report
from galapagos.utils.config_loader import load_profile, load_yaml


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["mock", "openai-codex", "codex_cli"], default="mock")
    parser.add_argument("--model", default="gpt-5.5")
    parser.add_argument("--reasoning-effort", default="low")
    parser.add_argument("--allow-network", action="store_true")
    parser.add_argument("--allow-codex-cli", action="store_true")
    parser.add_argument("--max-llm-calls", type=int, default=5)
    parser.add_argument("--bars", type=int, default=10)
    parser.add_argument("--profile", default="4h")
    parser.add_argument(
        "--prompt-mode",
        choices=["conservative", "balanced"],
        default="conservative",
    )
    args = parser.parse_args()

    if args.provider == "openai-codex":
        print(
            json.dumps(
                {
                    "provider_status": "unavailable",
                    "error": "Use provider=codex_cli for the V1.8C local CLI bridge.",
                },
                indent=2,
            )
        )
        return
    if args.provider == "codex_cli" and not args.allow_codex_cli:
        print(
            json.dumps(
                {
                    "provider_status": "refused",
                    "error": "codex_cli sample requires --allow-codex-cli.",
                },
                indent=2,
            )
        )
        return
    if args.provider == "codex_cli" and args.profile != "4h":
        print(
            json.dumps(
                {
                    "provider_status": "refused",
                    "error": "V1.8C codex_cli sample is limited to profile 4h.",
                },
                indent=2,
            )
        )
        return

    profile = load_profile(args.profile)
    data_path = find_latest_cached_ohlcv(profile["symbol"], profile["timeframe"])
    if data_path is None:
        raise RuntimeError("No cached OHLCV data found. Run download_historical_ohlcv first.")

    risk_config = load_yaml("configs/risk.yaml")
    llm_config = load_yaml("configs/llm.yaml")
    llm_config["allow_codex_cli_calls"] = bool(args.allow_codex_cli)
    llm_config["model"] = args.model
    llm_config["reasoning_effort"] = args.reasoning_effort
    llm_config.setdefault("codex_cli", {})["model"] = args.model
    llm_config.setdefault("codex_cli", {})["reasoning_effort"] = args.reasoning_effort

    warmup_bars = max(1, args.bars)
    codex_provider = CodexCLIProvider(llm_config) if args.provider == "codex_cli" else None
    result = ReplayEngine(
        profile=profile,
        data_path=data_path,
        risk_config=risk_config,
        initial_capital=10_000,
        policy="codex_cli" if args.provider == "codex_cli" else "llm_offline_conservative",
        warmup_bars=warmup_bars,
        force_close_at_end=True,
        llm_provider=codex_provider,
        max_llm_calls=args.max_llm_calls,
        prompt_mode=args.prompt_mode,
    ).run()
    decision_limit = args.max_llm_calls if args.provider == "codex_cli" else args.bars
    result["decisions"] = result["decisions"][:decision_limit]

    comparison = ReplayEngine(
        profile=profile,
        data_path=data_path,
        risk_config=risk_config,
        initial_capital=10_000,
        policy="llm_offline_conservative",
        warmup_bars=warmup_bars,
        force_close_at_end=True,
    ).run()
    comparison["decisions"] = comparison["decisions"][: len(result["decisions"])]

    breakout = ReplayEngine(
        profile=profile,
        data_path=data_path,
        risk_config=risk_config,
        initial_capital=10_000,
        policy="state_aware_breakout",
        warmup_bars=warmup_bars,
        force_close_at_end=True,
    ).run()
    breakout["decisions"] = breakout["decisions"][: len(result["decisions"])]

    report = write_codex_cli_sample_report(
        result=result,
        offline_comparison=comparison,
        breakout_comparison=breakout,
        output_dir=Path("reports/backtests"),
        version="V1.8C.1" if args.max_llm_calls >= 20 else "V1.8C",
    )
    output = {
        "provider": args.provider,
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "prompt_mode": args.prompt_mode,
        "llm_calls": result.get("llm_call_count", 0),
        "decisions": [decision["decision"] for decision in result["decisions"]],
        "metrics": result["metrics"],
        "offline_conservative_metrics": comparison["metrics"],
        "state_aware_breakout_metrics": breakout["metrics"],
        "report": report,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
