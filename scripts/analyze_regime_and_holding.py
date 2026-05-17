from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.analysis.regime_diagnostics import analyze_regime_and_holding


def main() -> None:
    analysis = analyze_regime_and_holding()
    output = Path("reports/evaluation")
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "regime_holding_diagnostics_v1_10_2.json"
    md_path = output / "regime_holding_diagnostics_v1_10_2.md"
    json_path.write_text(json.dumps(analysis, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(_markdown(analysis), encoding="utf-8")
    print(json.dumps({"markdown": str(md_path), "json": str(json_path), **analysis}, indent=2))


def _markdown(analysis: dict) -> str:
    lines = [
        "# Diagnostic regime et holding time Galapagos V1.10.2",
        "",
        "Analyse offline uniquement. Aucun appel Codex CLI. Aucun holdout execute.",
        "",
        f"- Verdicts : {analysis['verdicts']}",
        f"- Holdout execute : {analysis['holdout_executed']}",
        "",
        "## Regime par fenetre",
        "",
    ]
    for label, regime in analysis["window_regimes"].items():
        lines.extend(
            [
                f"### {label}",
                "",
                f"- Regime : {regime['regime_label']}",
                f"- Start/end price : {regime['start_price']:.2f} -> {regime['end_price']:.2f}",
                f"- Return : {regime['return_pct']:.2%}",
                f"- Max drawdown : {regime['max_drawdown']:.2%}",
                f"- Realized volatility : {regime['realized_volatility']:.2%}",
                f"- Slope : {regime['trend_slope']:.4f}",
                (
                    "- Candles above MA short/long : "
                    f"{regime['percent_candles_above_ma_short']:.2%} / "
                    f"{regime['percent_candles_above_ma_long']:.2%}"
                ),
                "",
            ]
        )
    lines.extend(
        [
            "## Performance side par regime",
            "",
            json.dumps(analysis["side_performance_by_regime"], indent=2, ensure_ascii=False),
            "",
            "## Holding time",
            "",
            json.dumps(analysis["holding_time"], indent=2, ensure_ascii=False),
            "",
            "## Hypotheses de duree de detention",
            "",
            json.dumps(analysis["holding_hypotheses"], indent=2, ensure_ascii=False),
            "",
            "## Reponses",
            "",
            json.dumps(analysis["answers"], indent=2, ensure_ascii=False),
            "",
            "## Recommandations",
            "",
            *[f"- {item}" for item in analysis["recommendations"]],
            "",
            "## Limites",
            "",
            "- Les simulations de holding time sont approximatives.",
            "- Les ledgers existants ne remplacent pas un nouveau backtest controle.",
            "- Le holdout reste verrouille.",
            "- Aucun module macro live et aucun levier ne sont implementes.",
            "",
            analysis["safety"],
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    main()
