from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.analysis.policy_comparison import compare_policies, policy_suite_answers
from galapagos.backtest.historical_data import cache_kraken_ohlcv, find_latest_cached_ohlcv
from galapagos.backtest.replay_engine import ReplayEngine
from galapagos.reports.llm_offline_decision_report import analyze_llm_offline_decisions
from galapagos.utils.config_loader import load_profile, load_yaml
from galapagos.utils.paths import project_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    report = run_suite(args.config)
    print(
        json.dumps(
            {
                "markdown": report["report_paths"]["markdown"],
                "json": report["report_paths"]["json"],
                "answers": report["answers"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )


def run_suite(config_path: str | Path) -> dict:
    config = load_yaml(config_path)
    output_dir = project_path(config.get("output_reports_dir", "reports/backtests"))
    output_dir.mkdir(parents=True, exist_ok=True)
    days = int(config.get("requested_days", 30))
    capital = float(config.get("initial_capital_per_profile", 10_000))
    force_close = bool(config.get("force_close_at_end", True))
    risk_config = load_yaml("configs/risk.yaml")
    results = []
    metadata = {}
    data_hashes = {}
    for profile_name in config.get("profiles", []):
        profile = load_profile(profile_name)
        data_path = find_latest_cached_ohlcv(profile["symbol"], profile["timeframe"])
        if data_path is None:
            data_path = cache_kraken_ohlcv(
                symbol=profile["symbol"],
                timeframe=profile["timeframe"],
                days=days,
            ).data_path
        metadata[profile["name"]] = _load_metadata(data_path)
        data_hashes[profile["name"]] = _file_hash(data_path)
        for policy in config.get("policies", []):
            results.append(
                ReplayEngine(
                    profile=profile,
                    data_path=data_path,
                    risk_config=risk_config,
                    initial_capital=capital,
                    policy=policy,
                    force_close_at_end=force_close,
                ).run()
            )
    rows = compare_policies(results)
    answers = policy_suite_answers(rows)
    llm_decisions = analyze_llm_offline_decisions(
        [
            {
                "policy": result["policy"],
                "raw_results": {result["profile"]: result},
            }
            for result in results
        ]
    )
    report = {
        "version": "V1.7",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "config": config,
        "metadata": metadata,
        "data_hashes": data_hashes,
        "results": results,
        "policy_comparison": rows,
        "answers": answers,
        "llm_offline_decision_analysis": llm_decisions,
        "security_confirmation": "Le systeme V1.7 ne peut toujours pas passer d'ordre reel.",
    }
    paths = _write_report(report, output_dir)
    report["report_paths"] = {key: str(value) for key, value in paths.items()}
    paths["json"].write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    return report


def _write_report(report: dict, output_dir: Path) -> dict[str, Path]:
    md_path = output_dir / "llm_offline_suite_v1_7.md"
    json_path = output_dir / "llm_offline_suite_v1_7.json"
    md_path.write_text(_markdown(report), encoding="utf-8")
    json_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    return {"markdown": md_path, "json": json_path}


def _markdown(report: dict) -> str:
    rows = report["policy_comparison"]
    answers = report["answers"]
    rankings = answers.get("rankings", {})
    lines = [
        "# Suite LLM offline Galapagos V1.7",
        "",
        f"- Genere le: {report['generated_at_utc']}",
        "- Les policies LLM offline simulent un agent. Elles ne prouvent pas un vrai edge.",
        "",
        "## Comparaison policies",
        "",
        "| Policy | Profil | Score prudent | PnL/jour | DD max | Trades/jour | "
        "Fees/jour | Slippage/jour | Rejects/jour | Win rate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['policy_name']} | {row['profile']} | "
            f"{_fmt(row['composite_prudent_score'])} | {_fmt(row['realized_pnl_per_day'])} | "
            f"{_fmt(row['max_drawdown'])} | {_fmt(row['trades_per_day'])} | "
            f"{_fmt(row['fees_per_day'])} | {_fmt(row['slippage_per_day'])} | "
            f"{_fmt(row['risk_rejected_per_day'])} | {_fmt(row['win_rate'])} |"
        )
    best_score = rankings.get("best_composite_prudent_score", {})
    best_llm = _best_llm(rows)
    best_baseline = _best_baseline(rows)
    lines.extend(
        [
            "",
            "## Synthese",
            "",
            f"- Meilleure baseline mecanique: `{best_baseline.get('policy_name')}` "
            f"sur `{best_baseline.get('profile')}`.",
            f"- Meilleure policy llm_offline: `{best_llm.get('policy_name')}` "
            f"sur `{best_llm.get('profile')}`.",
            f"- Meilleur score prudent global: `{best_score.get('policy_name')}` "
            f"sur `{best_score.get('profile')}`.",
            "- Profil recommande pour futur vrai LLM: celui qui combine score prudent, drawdown "
            "contenu et couts faibles.",
            "",
            "## Distribution decisions LLM offline",
            json.dumps(
                report["llm_offline_decision_analysis"]["decision_distribution_by_policy"],
                indent=2,
                ensure_ascii=False,
            ),
            "",
            "## Confirmation",
            "",
            "Le systeme V1.7 ne peut toujours pas passer d'ordre reel.",
        ]
    )
    return "\n".join(lines)


def _best_llm(rows: list[dict]) -> dict:
    candidates = [row for row in rows if row["policy_name"].startswith("llm_offline")]
    return max(candidates, key=lambda row: row["composite_prudent_score"], default={})


def _best_baseline(rows: list[dict]) -> dict:
    candidates = [
        row
        for row in rows
        if not row["policy_name"].startswith("llm_offline")
        and row["policy_name"] != "always_no_trade"
    ]
    return max(candidates, key=lambda row: row["composite_prudent_score"], default={})


def _fmt(value) -> str:
    return f"{value:.6f}" if isinstance(value, float) else str(value)


def _file_hash(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load_metadata(data_path: str | Path) -> dict:
    path = Path(data_path)
    files = sorted(path.parent.glob("metadata_*.json"))
    if not files:
        return {"metadata_status": "missing", "data_path": str(path)}
    return json.loads(files[-1].read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
