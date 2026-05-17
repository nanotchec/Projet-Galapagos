from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.bootstrap import permutation_test_signal_vs_random
from galapagos.research.labeling import add_research_labels
from galapagos.research.random_baselines import random_forward_returns
from galapagos.research.report_models import write_research_report
from galapagos.research.research_dataset import load_research_ohlcv, mechanical_signals


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="4h")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--random-seeds", type=int)
    parser.add_argument("--dataset")
    parser.add_argument("--output-version", default="v1_11")
    args = parser.parse_args()
    payload = run_random_baseline(
        profile=args.profile,
        seed=args.random_seeds or args.seed,
        dataset_path=args.dataset,
        output_version=args.output_version,
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


def run_random_baseline(
    *,
    profile: str,
    seed: int = 42,
    dataset_path: str | None = None,
    output_version: str = "v1_11",
) -> dict:
    data = _load_dataset(dataset_path) if dataset_path else load_research_ohlcv(profile)
    labels = add_research_labels(data)
    signals = mechanical_signals(profile, data)
    signal_returns = [
        float(value)
        for value in labels.loc[signals["index"], "forward_return_6bar"].dropna().tolist()
    ] if not signals.empty else []
    random_returns = random_forward_returns(
        labels,
        max(len(signal_returns), 1),
        horizon_column="forward_return_6bar",
        seed=seed,
    )
    permutation = permutation_test_signal_vs_random(
        signal_returns,
        random_returns,
        n_permutations=500,
        seed=seed,
    )
    payload = {
        "version": _display_version(output_version),
        "profile": profile,
        "dataset_path": dataset_path,
        "holdout_executed": False,
        "codex_cli_called": False,
        "signal_count": len(signal_returns),
        "random_count": len(random_returns),
        "permutation_test": permutation,
        "verdict": _verdict(permutation, len(signal_returns)),
        "warning": "Baseline aleatoire approximative; ce n'est pas une preuve statistique finale.",
    }
    write_research_report(
        name=f"random_baseline_{output_version}",
        payload=payload,
        title=f"Random Baseline {payload['version']}",
        lines=[
            "Comparaison offline des returns futurs des signaux avec des entrees aleatoires.",
            f"Verdict: {payload['verdict']}.",
        ],
    )
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


def _verdict(permutation: dict, sample_size: int) -> str:
    if sample_size < 100:
        return "NEED_MORE_DATA"
    if permutation.get("p_value", 1.0) < 0.05:
        return "WEAK_EDGE_BEFORE_COSTS"
    return "NO_EDGE_DETECTED"


if __name__ == "__main__":
    main()
