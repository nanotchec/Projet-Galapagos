from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def generate_backtest_report(
    result: dict[str, Any],
    output_dir: str | Path,
) -> dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    run_id = result["run_id"]
    md_path = output / f"backtest_{run_id}.md"
    json_path = output / f"backtest_{run_id}.json"
    md_path.write_text(_markdown(result), encoding="utf-8")
    json_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    return {"markdown": md_path, "json": json_path}


def _markdown(result: dict[str, Any]) -> str:
    lines = [
        f"# Rapport backtest Galapagos - {result['run_id']}",
        "",
        "## Avertissement",
        "Ce backtest teste la mecanique. Il ne prouve pas une profitabilite future.",
        "",
        "## Configuration",
        f"- Config: {result.get('config')}",
        f"- Periode: {result.get('period')}",
        f"- Source donnees: {result.get('data_source')}",
        f"- Hash donnees: {result.get('data_hashes')}",
        f"- Policy: {result.get('policy')}",
        f"- Force close at end: {result.get('force_close_at_end', False)}",
        "",
        "## Convention temporelle",
        "- Les timestamps OHLCV Kraken/CCXT sont traites comme ouvertures de bougie.",
        "- candle_open_timestamp = timestamp source.",
        "- candle_close_timestamp = candle_open_timestamp + timeframe.",
        "- decision_timestamp = candle_close_timestamp.",
        "- Une decision n'utilise une bougie que lorsque sa cloture est disponible.",
        "",
        "## Periode demandee vs periode reelle",
        json.dumps(result.get("metadata", {}), indent=2, ensure_ascii=False, default=str),
        "",
        "## Controles anti-fuite temporelle",
        json.dumps(result.get("anti_leakage", {}), indent=2, ensure_ascii=False, default=str),
        "",
        "## Metriques",
    ]
    for profile, metrics in result["metrics"].items():
        lines.append(f"### {profile}")
        raw = result.get("raw_results", {}).get(profile, {})
        if raw:
            lines.append(f"- Final equity: {raw.get('final_equity')}")
        for key, value in metrics.items():
            lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Comparaison backtest dediee",
            json.dumps(result.get("comparison", {}), indent=2, ensure_ascii=False, default=str),
        ]
    )
    lines.extend(
        [
            "",
            "## Limites",
            "- Donnees derivees historiques indisponibles/non rejouees en V1.5.1.",
            "- Les politiques mock servent a tester la mecanique, pas a prouver un edge.",
        ]
    )
    return "\n".join(lines)
