from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


from galapagos.research.benchmark import run_benchmarks
from galapagos.research.labeling import add_research_labels
from galapagos.research.random_baselines import random_forward_returns
from galapagos.research.regime_splits import (
    aggregate_signal_quality_by_regime,
    classify_regime_per_candle,
    classify_regime_window,
)
from galapagos.research.report_models import write_research_report
from galapagos.research.research_dataset import (
    load_research_ohlcv,
    mechanical_signals,
    research_windows,
)
from galapagos.research.signal_quality import analyze_signal_quality


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="4h")
    parser.add_argument("--windows", default="calibration,validation_1,validation_2")
    parser.add_argument("--include-cached-decisions", action="store_true")
    parser.add_argument("--include-holdout-metadata-only", action="store_true")
    parser.add_argument("--random-seeds", type=int, default=100)
    parser.add_argument("--dataset")
    parser.add_argument("--long-history", action="store_true")
    parser.add_argument("--min-samples-warning", type=int, default=100)
    parser.add_argument("--output-version", default="v1_11")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    payload = run_signal_quality(
        profile=args.profile,
        windows=[item.strip() for item in args.windows.split(",") if item.strip()],
        include_cached_decisions=args.include_cached_decisions,
        include_holdout_metadata_only=args.include_holdout_metadata_only,
        random_seeds=args.random_seeds,
        dataset_path=args.dataset,
        long_history=args.long_history,
        output_version=args.output_version,
        dry_run=args.dry_run,
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


def run_signal_quality(
    *,
    profile: str,
    windows: list[str],
    include_cached_decisions: bool = False,
    include_holdout_metadata_only: bool = False,
    random_seeds: int = 100,
    dataset_path: str | None = None,
    long_history: bool = False,
    output_version: str = "v1_11",
    dry_run: bool = False,
) -> dict:
    data = _load_dataset(dataset_path) if dataset_path else load_research_ohlcv(profile)
    all_windows = research_windows(data, ["calibration", "validation_1", "validation_2", "holdout"])
    selected_windows = list(windows)
    if include_holdout_metadata_only and "holdout" not in selected_windows:
        selected_windows.append("holdout")
    results: dict[str, dict] = {}
    benchmark_results: dict[str, dict] = {}
    regime_results: dict[str, dict] = {}
    signal_counts: dict[str, int] = {}
    for label in selected_windows:
        window_data = all_windows[label]
        if label == "holdout":
            regime_results[label] = classify_regime_window(window_data)
            continue
        labels = add_research_labels(window_data)
        signals = mechanical_signals(profile, window_data)
        random_returns = random_forward_returns(
            labels,
            max(len(signals), 1),
            horizon_column="forward_return_6bar",
            seed=random_seeds,
        )
        results[label] = analyze_signal_quality(labels, signals, random_returns=random_returns)
        benchmark_results[label] = run_benchmarks(window_data)
        regime_frame = classify_regime_per_candle(labels)
        regime_results[label] = {
            "window": classify_regime_window(window_data),
            "signal_quality": aggregate_signal_quality_by_regime(signals, regime_frame),
        }
        signal_counts[label] = len(signals)
    verdicts = sorted(
        {
            verdict
            for window_result in results.values()
            for verdict in window_result.get("verdicts", [])
        }
    )
    payload = {
        "version": _display_version(output_version),
        "dry_run": dry_run,
        "profile": profile,
        "dataset_path": dataset_path,
        "long_history": long_history,
        "windows": selected_windows,
        "holdout_executed": False,
        "codex_cli_called": False,
        "include_cached_decisions": include_cached_decisions,
        "signal_counts": signal_counts,
        "signal_quality": results,
        "benchmarks": benchmark_results,
        "regimes": regime_results,
        "verdicts": verdicts or ["NEED_MORE_DATA"],
        "scientific_warning": (
            "Ces resultats mesurent la qualite des signaux, pas une profitabilite."
        ),
    }
    _write_signal_quality_reports(payload, output_version=output_version)
    return payload


def _load_dataset(dataset_path: str | None):
    path = Path(dataset_path) if dataset_path else None
    if path is None:
        raise ValueError("dataset_path is required.")
    if path.suffix == ".parquet":
        return __import__("pandas").read_parquet(path)
    return __import__("pandas").read_csv(path)


def _display_version(output_version: str) -> str:
    if output_version == "v1_12_2":
        return "V1.12.2"
    if output_version == "v1_12_1":
        return "V1.12.1"
    if output_version == "v1_12":
        return "V1.12"
    return "V1.11"


def _write_signal_quality_reports(payload: dict, output_version: str = "v1_11") -> None:
    suffix = output_version
    lines = [
        f"{payload['version']} mesure la qualite des signaux avant optimisation.",
        "Aucun appel Codex CLI, aucun holdout, aucun ordre reel.",
        f"Fenetres analysees: {', '.join(payload['windows'])}.",
        f"Verdicts: {', '.join(payload['verdicts'])}.",
    ]
    write_research_report(
        name=f"signal_quality_{suffix}",
        payload=payload,
        title=f"Signal Quality Lab {payload['version']}",
        lines=lines,
    )
    write_research_report(
        name=f"benchmarks_{suffix}",
        payload={
            "version": payload["version"],
            "holdout_executed": False,
            "benchmarks": payload["benchmarks"],
            "warning": "Un PnL positif sur BTC ne vaut rien si buy-and-hold fait beaucoup mieux.",
        },
        title=f"Benchmarks {payload['version']}",
        lines=["Cash, buy-and-hold, trend filter et volatility targeting research-only."],
    )
    write_research_report(
        name=f"regime_signal_quality_{suffix}",
        payload={
            "version": payload["version"],
            "holdout_executed": False,
            "regimes": payload["regimes"],
        },
        title=f"Regime Signal Quality {payload['version']}",
        lines=["Agregation des signaux par regime de marche."],
    )


if __name__ == "__main__":
    main()
