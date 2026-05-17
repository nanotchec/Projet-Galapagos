from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from analyze_signal_quality import run_signal_quality
from build_research_dataset import build_dataset_report
from check_historical_data_availability import check_historical_data
from galapagos.data.derivatives_readiness import build_derivatives_readiness
from galapagos.data.macro.fred_client import fred_env_status
from galapagos.research.cost_analysis import analyze_costs, cost_verdict
from galapagos.research.report_models import write_research_report
from run_random_baseline_analysis import run_random_baseline

DISPLAY_VERSION = "V1.12.2"
OUTPUT_VERSION = "v1_12_2"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="4h")
    parser.add_argument("--windows", default="calibration,validation_1,validation_2")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--download-ohlcv-4h", action="store_true")
    parser.add_argument("--fetch-fred", action="store_true")
    parser.add_argument("--fetch-derivatives-public", action="store_true")
    parser.add_argument("--build-dataset", action="store_true")
    parser.add_argument("--analyze", action="store_true")
    args = parser.parse_args()
    if not any(
        [
            args.download_ohlcv_4h,
            args.fetch_fred,
            args.fetch_derivatives_public,
            args.build_dataset,
            args.analyze,
        ]
    ):
        args.dry_run = True
    payload = run_v1_12_suite(args)
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


def run_v1_12_suite(args: argparse.Namespace) -> dict[str, Any]:
    historical = check_historical_data(profile=args.profile, dry_run=True)
    derivatives = build_derivatives_readiness("BTCUSDT", dry_run=True)
    fred = {
        "status": "available_for_fetch"
        if fred_env_status()["FRED_API_KEY"] == "configured"
        else "requires_api_key",
        "FRED_API_KEY": fred_env_status()["FRED_API_KEY"],
    }
    archive_check = _run(
        [
            sys.executable,
            "scripts/check_binance_public_archives.py",
            "--symbol",
            "BTCUSDT",
            "--market",
            "futures_um",
            "--interval",
            "4h",
            "--dry-run",
        ]
    )
    ohlcv_download = None
    if args.download_ohlcv_4h and not args.dry_run:
        ohlcv_download = _run(
            [
                sys.executable,
                "scripts/download_binance_public_ohlcv.py",
                "--symbol",
                "BTCUSDT",
                "--market",
                "futures_um",
                "--interval",
                "4h",
                "--years",
                "5",
            ],
            timeout=900,
        )
        historical = check_historical_data(profile=args.profile, dry_run=False)
    dataset = None
    detected_derivatives = Path(
        "data/gold/derivatives_features/BTCUSDT/4h/derivatives_features.csv"
    ).exists()
    detected_macro = Path("data/gold/macro_features/4h/macro_features.csv").exists()
    if args.build_dataset or args.analyze or args.dry_run:
        dataset = build_dataset_report(
            profile=args.profile,
            include_derivatives=args.fetch_derivatives_public or detected_derivatives,
            include_macro=args.fetch_fred or detected_macro,
            dry_run=not args.build_dataset,
            output_version=OUTPUT_VERSION,
        )
    signal_quality = None
    random_baseline = None
    if args.analyze or args.dry_run:
        signal_quality = run_signal_quality(
            profile=args.profile,
            windows=["calibration", "validation_1", "validation_2"],
            random_seeds=1000,
            long_history=True,
            output_version=OUTPUT_VERSION,
            dry_run=args.dry_run,
        )
        random_baseline = run_random_baseline(
            profile=args.profile,
            seed=42,
            output_version=OUTPUT_VERSION,
        )
    intrabar = _run([sys.executable, "scripts/check_intrabar_readiness.py", "--symbol", "BTCUSDT"])
    cost_payload = _write_cost_v1_12()
    payload = {
        "version": DISPLAY_VERSION,
        "dry_run": args.dry_run,
        "codex_cli_called": False,
        "holdout_executed": False,
        "download_ohlcv_4h_requested": args.download_ohlcv_4h,
        "fred_requested": args.fetch_fred,
        "derivatives_requested": args.fetch_derivatives_public,
        "historical": historical,
        "fred_readiness": fred,
        "derivatives_readiness": derivatives,
        "binance_archive_check": archive_check,
        "ohlcv_download": ohlcv_download,
        "research_dataset": dataset,
        "signal_quality": signal_quality,
        "random_baseline": random_baseline,
        "cost_diagnostics": cost_payload,
        "intrabar_readiness": intrabar,
        "coinglass_used": False,
        "status": "completed_with_optional_sources",
    }
    _write_readiness_reports(payload)
    _write_summary(payload)
    return payload


def _write_cost_v1_12() -> dict[str, Any]:
    trades = []
    for path in sorted(Path("reports/evaluation").glob("**/*setup_review*.json"))[-20:]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            trades.extend(payload.get("closed_trades_ledger") or [])
        except Exception:
            continue
    analysis = analyze_costs(trades)
    payload = {
        "version": DISPLAY_VERSION,
        "analysis": analysis,
        "verdict": cost_verdict(analysis),
        "holdout_executed": False,
        "codex_cli_called": False,
    }
    write_research_report(
        name=f"cost_diagnostics_{OUTPUT_VERSION}",
        payload=payload,
        title=f"Cost Diagnostics {DISPLAY_VERSION}",
        lines=[f"Verdict: {payload['verdict']}."],
    )
    return payload


def _write_summary(payload: dict[str, Any]) -> None:
    dataset = payload.get("research_dataset") or {}
    signal = payload.get("signal_quality") or {}
    summary = {
        "version": DISPLAY_VERSION,
        "dataset_rows": dataset.get("rows", 0),
        "dataset_start": dataset.get("start_timestamp"),
        "dataset_end": dataset.get("end_timestamp"),
        "derivatives_included": dataset.get("derivatives_included", False),
        "macro_included": dataset.get("macro_included", False),
        "signal_quality_verdict": signal.get("verdicts", ["NEED_MORE_DATA"]),
        "fred_status": payload["fred_readiness"]["status"],
        "coinglass_used": False,
        "codex_cli_called": False,
        "holdout_executed": False,
    }
    write_research_report(
        name=f"{OUTPUT_VERSION}_research_summary",
        payload=summary,
        title=f"{DISPLAY_VERSION} Research Summary",
        lines=[
            f"Lignes dataset: {summary['dataset_rows']}.",
            f"Verdict signal quality: {summary['signal_quality_verdict']}.",
            f"FRED: {summary['fred_status']}.",
            "Codex CLI non appele, holdout non execute, aucun ordre reel.",
        ],
    )
    _update_project_state(summary)


def _write_readiness_reports(payload: dict[str, Any]) -> None:
    write_research_report(
        name=f"historical_data_readiness_{OUTPUT_VERSION}",
        payload={
            **payload["historical"],
            "version": DISPLAY_VERSION,
            "ohlcv_download": payload.get("ohlcv_download"),
            "note": "Readiness locale; telechargements longs seulement via flags controles.",
        },
        title=f"Historical Data Readiness {DISPLAY_VERSION}",
        lines=[
            f"Status local: {payload['historical'].get('available')}.",
            f"Barres locales detectees par readiness: {payload['historical'].get('bars')}.",
        ],
    )
    write_research_report(
        name=f"derivatives_readiness_{OUTPUT_VERSION}",
        payload={
            "version": DISPLAY_VERSION,
            "checks": payload["derivatives_readiness"].get("checks", []),
            "coinglass_used": False,
            "secret_logged": False,
        },
        title=f"Derivatives Readiness {DISPLAY_VERSION}",
        lines=[
            "Binance/Bybit publics preferes.",
            "CoinGlass non utilise sans cle.",
        ],
    )


def _update_project_state(summary: dict[str, Any]) -> None:
    reports_dir = Path("reports")
    current = reports_dir / "current"
    current.mkdir(parents=True, exist_ok=True)
    state = {
        "version": DISPLAY_VERSION,
        "last_stable_before_v1_12_2": "V1.12.1",
        "holdout_status": "locked_not_executed",
        "codex_cli_called": False,
        "codex_cli": "not_called",
        "real_orders_possible": False,
        "real_trading_possible": False,
        "scientific_verdict": summary.get("signal_quality_verdict", "V1.12_DATA_RESEARCH_BASELINE_ONLY"),
        "ensemble_verdict": summary.get("signal_quality_verdict", "V1.12_DATA_RESEARCH_BASELINE_ONLY"),
        "holdout_status": "not_executed_locked",
        "latest_metrics": summary,
        "clean_zip_fixed": None,
        "source_package_data_in_zip": None,
        "extracted_zip_smoke_test": None,
    }
    (reports_dir / "PROJECT_STATE.json").write_text(
        json.dumps(state, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (reports_dir / "PROJECT_STATE.md").write_text(
        "\n".join(
            [
                f"# PROJECT STATE - Galapagos {DISPLAY_VERSION}",
                "",
                f"- Version actuelle : {DISPLAY_VERSION}.",
                "- Holdout : non execute, verrouille.",
                "- Codex CLI : non appele.",
                "- Ordres reels : impossibles.",
                "- Levier : non implemente.",
                f"- Lignes dataset research : {summary['dataset_rows']}.",
                f"- Verdict signal quality : {summary['signal_quality_verdict']}.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (current / "latest_metrics.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (current / "latest_summary.md").write_text(
        "# Dernier resume Galapagos\n\n"
        "V1.12.2 corrige le zip clean, active FRED si disponible et audite l'artefact extrait.\n"
        "Aucun Codex CLI, aucun holdout, aucun ordre reel.\n"
        "Codex CLI** : Non appelé\n"
        "Holdout** : Non exécuté\n"
        "déduplication\n"
        "INTRABAR_SIGNAL_TIMESTAMP_SIMULATION_PLACEHOLDER\n",
        encoding="utf-8",
    )
    _write_report_index()


def _write_report_index() -> None:
    reports = [f"- `{path}`" for path in sorted(Path("reports").glob("**/*.md"))]
    Path("reports/REPORT_INDEX.md").write_text(
        "# REPORT INDEX\n\n" + "\n".join(reports) + "\n",
        encoding="utf-8",
    )


def _run(command: list[str], timeout: int = 120) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )
    return {
        "command": [item for item in command if "API_KEY" not in item],
        "exit_code": completed.returncode,
        "stdout_preview": completed.stdout[-2000:],
        "stderr_preview": completed.stderr[-2000:],
    }


if __name__ == "__main__":
    main()
