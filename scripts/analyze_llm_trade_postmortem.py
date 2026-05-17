from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.analysis.llm_trade_postmortem import analyze_llm_trade_postmortem  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="reports/backtests/codex_setup_review_v1_8C_9.json",
    )
    parser.add_argument("--output-dir", default="reports/diagnostics")
    parser.add_argument("--output-prefix", default="llm_trade_postmortem_v1_8C_9")
    args = parser.parse_args()
    analysis = analyze_llm_trade_postmortem(args.input)
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / f"{args.output_prefix}.json"
    md_path = output / f"{args.output_prefix}.md"
    json_path.write_text(json.dumps(analysis, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(_markdown(analysis), encoding="utf-8")
    print(json.dumps({"markdown": str(md_path), "json": str(json_path), **analysis}, indent=2))


def _markdown(analysis: dict) -> str:
    lines = [
        "# Post-mortem decisions GPT-5.5 V1.8C.9",
        "",
        f"- Source : {analysis['source_report']}",
        f"- Version source : {analysis['source_version']}",
        f"- Source de verite : {analysis['source_of_truth']}",
        f"- Trades analyses : {analysis['trades_analyzed']}",
        f"- Ledger matches official : {analysis['ledger_pnl_matches_official']}",
        f"- Ledger PnL delta : {analysis['ledger_pnl_delta']}",
        f"- PnL realise officiel du run source : {analysis['source_report_realized_pnl']}",
        f"- Frais officiels du run source : {analysis['source_report_fees']}",
        f"- Slippage officiel du run source : {analysis['source_report_slippage']}",
        f"- PnL net total : {analysis['total_net_pnl']}",
        f"- PnL brut avant frais : {analysis['total_gross_pnl_before_fees']}",
        f"- Frais : {analysis['total_fees']}",
        f"- Slippage : {analysis['total_slippage']}",
        f"- Trades gagnants/perdants : {analysis['winning_trades']} / {analysis['losing_trades']}",
        f"- Gagnants sans frais/slippage : {analysis['would_win_without_costs']}",
        "",
        "## Causes probables de perte",
        "",
        json.dumps(analysis["loss_causes"], indent=2, ensure_ascii=False),
        "",
        "## Filtres simules",
        "",
        json.dumps(analysis["filter_results"], indent=2, ensure_ascii=False),
        "",
        "## Agregations",
        "",
        json.dumps(analysis["aggregations"], indent=2, ensure_ascii=False),
        "",
        "## Trades acceptes",
        "",
    ]
    for trade in analysis["trades"]:
        lines.extend(
            [
                f"### {trade['candidate_id']}",
                "",
                f"- Timestamp : {trade['timestamp']}",
                f"- Decision : {trade['decision']}",
                f"- Setup quality : {trade['setup_quality']} ({trade['setup_quality_score']})",
                f"- Confidence : {trade['confidence']}",
                f"- Risk fraction : {trade['risk_fraction']}",
                f"- Strategy : {trade['strategy']}",
                f"- Baseline : {trade['candidate_baseline_source']}",
                f"- Entry/exit : {trade['entry_price']} -> {trade['exit_price']}",
                f"- Stop/TP : {trade['stop_loss']} / {trade['take_profit']}",
                f"- Risk/reward : {trade['risk_reward_ratio']}",
                f"- Close reason : {trade['close_reason']}",
                f"- PnL brut/net : {trade['gross_pnl']} / {trade['net_pnl']}",
                f"- Fees/slippage : {trade['fees']} / {trade['slippage']}",
                f"- Duree barres : {trade['duration_bars']}",
                f"- Causes : {trade['probable_loss_causes']}",
                f"- Reasoning : {trade['reasoning_summary']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Prompt hardening recommendations",
            "",
            *[f"- {item}" for item in analysis["prompt_hardening_recommendations"]],
            "",
            "## Limites",
            "",
            *[f"- {item}" for item in analysis["limitations"]],
            "",
            analysis["safety"],
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    main()
