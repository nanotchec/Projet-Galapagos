from __future__ import annotations

from typing import Any


def build_dataset_datacard_v9_41(report: dict[str, Any]) -> str:
    row_counts = report.get("row_counts", {})
    valid_counts = report.get("valid_row_counts", {})
    invalid_counts = report.get("invalid_row_counts", {})
    lines = [
        "# Datacard V9.41 - Dataset OHLCV + AggTrades 5Y",
        "",
        "## Objet",
        "Dataset supervise offline construit a partir du feature store V9.37 valide V9.38 et des labels V9.40.",
        "",
        "## Fenetre",
        f"- Fenetre : `{report.get('target_window', {}).get('start')} -> {report.get('target_window', {}).get('end')}`.",
        f"- Target principal : `{report.get('target_name')}`.",
        "- Splits temporels : train 60 %, validation 20 %, test 20 %, shuffle false.",
        "- Walk-forward group : `calendar_month`.",
        "- Purge/embargo : `none_v9_41_preview`.",
        "",
        "## Lignes",
    ]
    for timeframe in report.get("timeframes", []):
        lines.append(
            f"- `{timeframe}` : rows `{row_counts.get(timeframe)}`, valides target `{valid_counts.get(timeframe)}`, invalides `{invalid_counts.get(timeframe)}`."
        )
    lines.extend(
        [
            "",
            "## Causalite",
            f"- Leakage guard : `{report.get('leakage_guard', {}).get('status')}`.",
            "- Les features doivent etre disponibles avant ou a `decision_ts`.",
            "- Les labels valides doivent etre disponibles strictement apres `decision_ts`.",
            "- Les labels diagnostics sont conserves comme colonnes d'audit, pas comme features.",
            "",
            "## Limites",
            "- Ce dataset ne valide aucun edge, aucune strategie et aucun signal.",
            "- Aucun ML, walk-forward, backtest, PnL, Sharpe, drawdown ou modele persistant n'est produit.",
            "- Les lignes warmup/tail sans target H1 valide sont conservees avec `row_valid_for_dataset=false`.",
            "",
            "## Decision",
            f"- Decision V9.41 : `{report.get('decision')}`.",
            f"- Qualite : `{report.get('quality_status')}`.",
            f"- Couverture : `{report.get('coverage_status')}`.",
        ]
    )
    return "\n".join(lines) + "\n"
