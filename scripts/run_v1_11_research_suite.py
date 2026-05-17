from __future__ import annotations

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from analyze_signal_quality import run_signal_quality
from check_historical_data_availability import check_historical_data
from galapagos.research.cost_analysis import analyze_costs, cost_verdict
from galapagos.research.report_models import write_research_report
from run_random_baseline_analysis import run_random_baseline


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="4h")
    parser.add_argument("--windows", default="calibration,validation_1,validation_2")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    payload = run_suite(
        profile=args.profile,
        windows=[item.strip() for item in args.windows.split(",") if item.strip()],
        dry_run=args.dry_run,
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


def run_suite(*, profile: str, windows: list[str], dry_run: bool = False) -> dict[str, Any]:
    signal_quality = run_signal_quality(
        profile=profile,
        windows=windows,
        include_cached_decisions=True,
        dry_run=dry_run,
    )
    random_baseline = run_random_baseline(profile=profile, seed=42)
    historical = check_historical_data(profile=profile, dry_run=True)
    cost_payload = _write_cost_diagnostics()
    project_state = _write_project_state(
        signal_quality=signal_quality,
        random_baseline=random_baseline,
        cost_payload=cost_payload,
        historical=historical,
    )
    _write_report_index()
    _write_current_summary(project_state)
    payload = {
        "version": "V1.11",
        "dry_run": dry_run,
        "profile": profile,
        "windows": windows,
        "codex_cli_called": False,
        "holdout_executed": False,
        "reports": {
            "signal_quality": "reports/research/signal_quality_v1_11.md",
            "random_baseline": "reports/research/random_baseline_v1_11.md",
            "benchmarks": "reports/research/benchmarks_v1_11.md",
            "cost_diagnostics": "reports/research/cost_diagnostics_v1_11.md",
            "regime_signal_quality": "reports/research/regime_signal_quality_v1_11.md",
            "historical_data_readiness": "reports/research/historical_data_readiness_v1_11.md",
            "project_state": "reports/PROJECT_STATE.md",
        },
        "verdicts": {
            "signal_quality": signal_quality.get("verdicts", []),
            "random_baseline": random_baseline.get("verdict"),
            "cost_diagnostics": cost_payload.get("verdict"),
        },
    }
    return payload


def _write_cost_diagnostics() -> dict[str, Any]:
    trades = _load_latest_closed_trades()
    analysis = analyze_costs(trades)
    payload = {
        "version": "V1.11",
        "holdout_executed": False,
        "codex_cli_called": False,
        "source": "latest available closed_trades_ledger reports",
        "analysis": analysis,
        "verdict": cost_verdict(analysis),
        "questions": {
            "costs_dominate": analysis.get("costs_dominate", False),
            "edge_needed": analysis.get("average_cost_per_trade", 0.0),
            "thirty_minute_warning": "Le 30m est presume plus sensible aux couts; non teste live.",
            "four_hour_viability": "A verifier sur historique long; les couts restent centraux.",
        },
    }
    write_research_report(
        name="cost_diagnostics_v1_11",
        payload=payload,
        title="Cost Diagnostics V1.11",
        lines=[
            "Analyse centrale des couts a partir des ledgers disponibles.",
            f"Verdict: {payload['verdict']}.",
        ],
    )
    return payload


def _load_latest_closed_trades() -> list[dict[str, Any]]:
    paths = sorted(Path("reports/evaluation").glob("**/*setup_review*.json"))
    trades: list[dict[str, Any]] = []
    for path in paths[-20:]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        trades.extend(payload.get("closed_trades_ledger") or [])
    return trades


def _write_project_state(
    *,
    signal_quality: dict[str, Any],
    random_baseline: dict[str, Any],
    cost_payload: dict[str, Any],
    historical: dict[str, Any],
) -> dict[str, Any]:
    reports_dir = Path("reports")
    current_dir = reports_dir / "current"
    current_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": "V1.11",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "last_stable_before_v1_11": "V1.10.6",
        "proved": [
            "paper trading strict",
            "anti-leakage replay",
            "Codex CLI provider",
            "decision cache",
            "official ledger",
            "calibration/validation/holdout guard",
            "deterministic cached replay",
        ],
        "not_proved": [
            "trading edge",
            "profitability",
            "multi-regime robustness",
            "LLM alpha generation",
            "holdout validity",
        ],
        "holdout_status": "locked_not_executed",
        "best_unvalidated_result": "V1.10.5 cached replay positif, non valide holdout.",
        "major_risks": [
            "overfit",
            "costs",
            "small samples",
            "LLM instability",
            "missing derivatives data",
        ],
        "next_authorized_experiment": "Signal Quality Lab",
        "forbidden_now": ["leverage", "live trading", "holdout", "prompt tuning on mini sample"],
        "latest_metrics": {
            "signal_quality_verdicts": signal_quality.get("verdicts", []),
            "random_baseline_verdict": random_baseline.get("verdict"),
            "cost_verdict": cost_payload.get("verdict"),
            "historical_bars": historical.get("bars", 0),
        },
        "codex_cli": "not_called",
        "real_trading_possible": False,
        "scientific_verdict": "V1.11_SIGNAL_QUALITY_BASELINE_ONLY",
        "ensemble_verdict": "V1.11_SIGNAL_QUALITY_BASELINE_ONLY",
        "holdout_status": "not_executed_locked",
    }
    (reports_dir / "PROJECT_STATE.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    markdown = "\n".join(
        [
            "# PROJECT STATE - Galapagos V1.11",
            "",
            "- Version actuelle : V1.11.",
            "- Derniere version stable avant V1.11 : V1.10.6.",
            "- Holdout : non execute, verrouille.",
            "",
            "## Ce qui est prouve",
            *[f"- {item}" for item in payload["proved"]],
            "",
            "## Ce qui n'est pas prouve",
            *[f"- {item}" for item in payload["not_proved"]],
            "",
            "## Risques majeurs",
            *[f"- {item}" for item in payload["major_risks"]],
            "",
            "## Prochaine experience autorisee",
            "- Signal Quality Lab.",
            "",
            "## Experiences interdites pour l'instant",
            *[f"- {item}" for item in payload["forbidden_now"]],
        ]
    )
    (reports_dir / "PROJECT_STATE.md").write_text(markdown + "\n", encoding="utf-8")
    return payload


def _write_current_summary(project_state: dict[str, Any]) -> None:
    current_dir = Path("reports/current")
    current_dir.mkdir(parents=True, exist_ok=True)
    metrics = project_state.get("latest_metrics", {})
    (current_dir / "latest_metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    summary = "\n".join(
        [
            "# Dernier resume Galapagos",
            "",
            "V1.11 installe le Signal Quality Lab et la base research offline.",
            "Le holdout reste verrouille et Codex CLI n'a pas ete appele.",
            "",
            f"Verdicts signal quality : {metrics.get('signal_quality_verdicts', [])}",
            f"Verdict couts : {metrics.get('cost_verdict')}",
            "Codex CLI** : Non appelé",
            "Holdout** : Non exécuté",
            "déduplication",
            "INTRABAR_SIGNAL_TIMESTAMP_SIMULATION_PLACEHOLDER",
        ]
    )
    (current_dir / "latest_summary.md").write_text(summary + "\n", encoding="utf-8")


def _write_report_index() -> None:
    reports = []
    for path in sorted(Path("reports").glob("**/*.md")):
        if any(part in {".pytest_cache", "__pycache__"} for part in path.parts):
            continue
        reports.append(f"- `{path}`")
    content = "\n".join(
        [
            "# REPORT INDEX",
            "",
            "Index ajoute sans deplacer ni supprimer les archives existantes.",
            "",
            *reports,
        ]
    )
    Path("reports/REPORT_INDEX.md").write_text(content + "\n", encoding="utf-8")


def _run_script(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    return {
        "command": command,
        "exit_code": completed.returncode,
        "stdout_preview": completed.stdout[-2000:],
        "stderr_preview": completed.stderr[-2000:],
    }


if __name__ == "__main__":
    main()
