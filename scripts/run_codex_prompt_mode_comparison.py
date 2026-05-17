from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.agent.llm_providers import CodexCLIProvider
from galapagos.backtest.historical_data import find_latest_cached_ohlcv
from galapagos.backtest.replay_engine import ReplayEngine
from galapagos.reports.codex_cli_report import analyze_codex_cli_decisions
from galapagos.utils.config_loader import load_profile, load_yaml


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="4h")
    parser.add_argument("--provider", choices=["codex_cli", "mock"], default="codex_cli")
    parser.add_argument("--bars", type=int, default=20)
    parser.add_argument("--modes", default="conservative,balanced")
    parser.add_argument("--allow-codex-cli", action="store_true")
    parser.add_argument("--model", default="gpt-5.5")
    parser.add_argument("--reasoning-effort", default="low")
    args = parser.parse_args()
    if args.profile != "4h":
        raise RuntimeError("V1.8C.2 real Codex CLI comparison is limited to profile 4h.")
    modes = [mode.strip() for mode in args.modes.split(",") if mode.strip()]
    if any(mode not in {"conservative", "balanced"} for mode in modes):
        raise RuntimeError("Modes must be conservative and/or balanced.")
    if args.provider == "codex_cli" and len(modes) * args.bars > 40:
        raise RuntimeError("V1.8C.2 comparison is limited to 40 Codex CLI calls.")
    if args.provider == "codex_cli" and not args.allow_codex_cli:
        raise RuntimeError("Codex CLI comparison requires --allow-codex-cli.")

    profile = load_profile(args.profile)
    data_path = find_latest_cached_ohlcv(profile["symbol"], profile["timeframe"])
    if data_path is None:
        raise RuntimeError("No cached OHLCV data found. Run download_historical_ohlcv first.")
    risk_config = load_yaml("configs/risk.yaml")
    llm_config = load_yaml("configs/llm.yaml")
    llm_config["allow_codex_cli_calls"] = True
    llm_config["model"] = args.model
    llm_config["reasoning_effort"] = args.reasoning_effort
    llm_config.setdefault("codex_cli", {})["model"] = args.model
    llm_config.setdefault("codex_cli", {})["reasoning_effort"] = args.reasoning_effort

    results = {}
    analyses = {}
    for mode in modes:
        result = ReplayEngine(
            profile=profile,
            data_path=data_path,
            risk_config=risk_config,
            initial_capital=10_000,
            policy="codex_cli" if args.provider == "codex_cli" else "llm_offline_conservative",
            warmup_bars=max(1, args.bars),
            force_close_at_end=True,
            llm_provider=CodexCLIProvider(llm_config) if args.provider == "codex_cli" else None,
            max_llm_calls=args.bars if args.provider == "codex_cli" else None,
            prompt_mode=mode,
        ).run()
        result["decisions"] = result["decisions"][: args.bars]
        results[mode] = result

    offline = ReplayEngine(
        profile=profile,
        data_path=data_path,
        risk_config=risk_config,
        initial_capital=10_000,
        policy="llm_offline_conservative",
        warmup_bars=max(1, args.bars),
        force_close_at_end=True,
    ).run()
    offline["decisions"] = offline["decisions"][: args.bars]

    for mode, result in results.items():
        analyses[mode] = analyze_codex_cli_decisions(result, offline)
        analyses[mode]["version"] = "V1.8C.2"
        analyses[mode]["prompt_mode"] = mode

    report = {
        "version": "V1.8C.2",
        "profile": profile["name"],
        "bars": args.bars,
        "total_codex_cli_calls": sum(
            analysis["total_codex_cli_calls"] for analysis in analyses.values()
        ),
        "provider": args.provider,
        "modes": analyses,
        "comparison": _compare_modes(analyses),
        "offline_conservative_metrics": offline["metrics"],
        "limitations": [
            "Sample court, limite a 40 appels Codex CLI.",
            "Profil 4h uniquement.",
            "Aucun resultat ne prouve une profitabilite.",
        ],
        "safety": "Le systeme V1.8C.2 ne peut toujours pas passer d'ordre reel.",
    }
    output_dir = Path("reports/backtests")
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "codex_prompt_mode_comparison_v1_8C_2.json"
    md_path = output_dir / "codex_prompt_mode_comparison_v1_8C_2.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(_markdown(report), encoding="utf-8")
    print(
        json.dumps(
            {"markdown": str(md_path), "json": str(json_path), **report},
            indent=2,
            ensure_ascii=False,
        )
    )


def _compare_modes(analyses: dict[str, dict]) -> dict:
    conservative = analyses.get("conservative", {})
    balanced = analyses.get("balanced", {})
    return {
        "decision_distribution_delta": {
            "conservative": conservative.get("decision_distribution", {}),
            "balanced": balanced.get("decision_distribution", {}),
        },
        "active_decision_rate_delta_balanced_minus_conservative": (
            float(balanced.get("active_decision_rate") or 0.0)
            - float(conservative.get("active_decision_rate") or 0.0)
        ),
        "balanced_assessment": _assess_balanced(balanced),
    }


def _assess_balanced(balanced: dict) -> str:
    active_rate = float(balanced.get("active_decision_rate") or 0.0)
    risk_rejects = int(balanced.get("risk_rejects") or 0)
    if risk_rejects:
        return "trop permissif"
    if active_rate == 0:
        return "encore trop prudent"
    if active_rate <= 0.25:
        return "raisonnable"
    return "potentiellement trop permissif"


def _markdown(report: dict) -> str:
    lines = [
        "# Comparaison prompt modes Codex CLI V1.8C.2",
        "",
        f"- Profil : {report['profile']}",
        f"- Bougies/contextes : {report['bars']}",
        f"- Appels Codex CLI : {report['total_codex_cli_calls']}",
        "",
        "## Modes",
    ]
    for mode, analysis in report["modes"].items():
        lines.extend(
            [
                "",
                f"### {mode}",
                f"- JSON valid rate : {analysis['valid_json_rate']}",
                f"- Duree moyenne : {analysis['average_duration_seconds']:.3f}s",
                f"- Distribution : {analysis['decision_distribution']}",
                f"- Active decision rate : {analysis['active_decision_rate']}",
                f"- Risk rejects : {analysis['risk_rejects']}",
                f"- PnL : {analysis['metrics'].get('realized_pnl')}",
                f"- Setup quality : {analysis.get('setup_quality_distribution', {})}",
                f"- Raisons NO_TRADE : {analysis.get('top_reasoning_categories', {})}",
            ]
        )
    lines.extend(
        [
            "",
            "## Comparaison",
            "",
            json.dumps(report["comparison"], indent=2, ensure_ascii=False),
            "",
            "## Offline conservative",
            "",
            json.dumps(report["offline_conservative_metrics"], indent=2, ensure_ascii=False),
            "",
            "## Conclusion",
            "",
            f"Balanced est evalue : {report['comparison']['balanced_assessment']}.",
            "Ce test evalue le comportement et les garde-fous, pas une profitabilite.",
            report["safety"],
        ]
    )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
