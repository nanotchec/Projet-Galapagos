from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

try:
    from _bootstrap import bootstrap_src_path
except ModuleNotFoundError:
    from scripts._bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.analysis.policy_comparison import compare_policies, policy_suite_answers
from galapagos.backtest.historical_data import cache_kraken_ohlcv, find_latest_cached_ohlcv
from galapagos.backtest.replay_engine import ReplayEngine
from galapagos.utils.config_loader import load_profile, load_yaml
from galapagos.utils.paths import project_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    payload = run_baseline_suite(args.config)
    print(
        json.dumps(
            {
                "markdown": payload["report_paths"]["markdown"],
                "json": payload["report_paths"]["json"],
                "answers": payload["answers"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )


def run_baseline_suite(config_path: str | Path) -> dict:
    config = load_yaml(config_path)
    policies = list(config.get("policies", []))
    profiles = list(config.get("profiles", []))
    requested_days = int(config.get("requested_days", 30))
    output_dir = project_path(config.get("output_reports_dir", "reports/backtests"))
    output_dir.mkdir(parents=True, exist_ok=True)
    capital = float(config.get("initial_capital_per_profile", 10_000))
    force_close = bool(config.get("force_close_at_end", True))
    risk_config = load_yaml("configs/risk.yaml")

    results: list[dict] = []
    metadata: dict[str, dict] = {}
    data_hashes: dict[str, str] = {}
    for profile_name in profiles:
        profile = load_profile(profile_name)
        data_path = find_latest_cached_ohlcv(profile["symbol"], profile["timeframe"])
        if data_path is None:
            data_path = cache_kraken_ohlcv(
                symbol=profile["symbol"],
                timeframe=profile["timeframe"],
                days=requested_days,
            ).data_path
        metadata[profile["name"]] = _load_metadata(data_path)
        data_hashes[profile["name"]] = _file_hash(data_path)
        for policy in policies:
            result = ReplayEngine(
                profile=profile,
                data_path=data_path,
                risk_config=risk_config,
                initial_capital=capital,
                policy=policy,
                force_close_at_end=force_close,
            ).run()
            results.append(result)

    rows = compare_policies(results)
    answers = policy_suite_answers(rows)
    generated_at = datetime.now(UTC).isoformat()
    report = {
        "version": "V1.6",
        "suite_name": config.get("suite_name", "baseline_suite"),
        "generated_at_utc": generated_at,
        "config": config,
        "metadata": metadata,
        "data_hashes": data_hashes,
        "results": results,
        "policy_comparison": rows,
        "answers": answers,
        "security_confirmation": "Le systeme V1.6 ne peut toujours pas passer d'ordre reel.",
    }
    paths = write_baseline_report(report, output_dir)
    report["report_paths"] = {key: str(value) for key, value in paths.items()}
    paths["json"].write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    return report


def write_baseline_report(report: dict, output_dir: str | Path) -> dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    md_path = output / "baseline_suite_v1_6.md"
    json_path = output / "baseline_suite_v1_6.json"
    md_path.write_text(_markdown(report), encoding="utf-8")
    json_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    return {"markdown": md_path, "json": json_path}


def _markdown(report: dict) -> str:
    rows = report["policy_comparison"]
    answers = report["answers"]
    lines = [
        "# Baselines mecaniques Galapagos V1.6",
        "",
        f"- Genere le: {report['generated_at_utc']}",
        "- Mode: backtest / paper uniquement",
        "- Avertissement: ces policies sont des baselines mecaniques, pas des strategies finales.",
        "",
        "## Donnees",
    ]
    for profile, metadata in report["metadata"].items():
        lines.extend(
            [
                f"### {profile}",
                f"- Source: {metadata.get('source')}",
                f"- Symbole: {metadata.get('symbol')}",
                f"- Timeframe: {metadata.get('timeframe')}",
                f"- Jours demandes: {metadata.get('requested_days')}",
                f"- Jours effectifs approx.: {metadata.get('approx_actual_days')}",
                f"- Bougies: {metadata.get('rows')}",
                f"- Hash: `{metadata.get('data_hash')}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Comparaison policies",
            "",
            "| Policy | Profil | PnL/jour | Trades/jour | DD max | Profit factor | "
            "Expectancy | Fees/jour | Slippage/jour | Risk rejects/jour | Exposure |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['policy_name']} | {row['profile']} | "
            f"{_fmt(row['realized_pnl_per_day'])} | {_fmt(row['trades_per_day'])} | "
            f"{_fmt(row['max_drawdown'])} | {_fmt(row['profit_factor'])} | "
            f"{_fmt(row['expectancy'])} | {_fmt(row['fees_per_day'])} | "
            f"{_fmt(row['slippage_per_day'])} | {_fmt(row['risk_rejected_per_day'])} | "
            f"{_fmt(row['exposure_time'])} |"
        )
    least = answers.get("least_losing_policy") or {}
    lowest_reject = answers.get("lowest_risk_reject_policy") or {}
    reference = answers.get("recommended_llm_reference_baseline") or {}
    lines.extend(
        [
            "",
            "## Reponses",
            "",
            f"1. Policy qui perd le moins: `{least.get('policy_name')}` "
            f"sur `{least.get('profile')}` avec PnL/jour "
            f"{_fmt(least.get('realized_pnl_per_day'))}.",
            f"2. Policy avec le moins de risk rejects: `{lowest_reject.get('policy_name')}` "
            f"sur `{lowest_reject.get('profile')}`.",
            "3. Les state-aware policies reduisent les refus: "
            f"{answers.get('state_aware_reduces_rejects')}.",
            "4. Le 30m reste couteux si les entrees sont frequentes: comparer fees/jour et "
            "slippage/jour dans le tableau.",
            "5. Le 4h est plus stable si son drawdown moyen et ses couts/jour restent inferieurs.",
            "6. Les frais/slippage restent destructeurs pour les policies qui tradent trop.",
            "7. Baseline de reference recommandee: voir la policy qui combine PnL/jour le moins "
            "negatif, peu de rejects et drawdown contenu.",
            f"   Recommendation actuelle: `{reference.get('policy_name')}` "
            f"sur `{reference.get('profile')}`.",
            "",
            "## Confirmation",
            "",
            "Le systeme V1.6 ne peut toujours pas passer d'ordre reel.",
        ]
    )
    return "\n".join(lines)


def _fmt(value) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    if value is None:
        return "n/a"
    return str(value)


def _file_hash(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load_metadata(data_path: str | Path) -> dict:
    path = Path(data_path)
    metadata_files = sorted(path.parent.glob("metadata_*.json"))
    if not metadata_files:
        return {"data_path": str(path), "metadata_status": "missing"}
    for candidate in reversed(metadata_files):
        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if data.get("data_path") == str(path):
            return data
    return json.loads(metadata_files[-1].read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
