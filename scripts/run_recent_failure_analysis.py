"""Script orchestrator for recent regime failure analysis (V1.17+).

Runs all the diagnostic modules on the recent window failure and produces
a synthesized recommendation.

V1.17.1: In non-dry-run mode, the dataset MUST exist. Missing dataset
causes a hard error (exit 1) instead of generating SKIPPED reports.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

import pandas as pd

from galapagos.research.failure_analysis.cost_failure import run_cost_analysis
from galapagos.research.failure_analysis.data_gap_analysis import run_data_gap_analysis
from galapagos.research.failure_analysis.feature_drift import run_feature_drift_analysis
from galapagos.research.failure_analysis.horizon_diagnostics import run_horizon_diagnostics
from galapagos.research.failure_analysis.label_diagnostics import run_label_diagnostics
from galapagos.research.failure_analysis.recent_window import run_recent_window_analysis
from galapagos.research.failure_analysis.recommendation_engine import run_recommendation_engine
from galapagos.research.failure_analysis.regime_failure import run_regime_analysis


def _version_suffix(version: str) -> str:
    """Normalize version string into a file-name suffix, e.g. 'v1.17.1' -> 'v1_17_1'."""
    return version.replace(".", "_")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run recent failure analysis suite.")
    parser.add_argument("--dataset", required=True, help="Path to the dataset parquet file.")
    parser.add_argument("--ensemble-report", required=True, help="Path to the ensemble report json.")
    parser.add_argument("--version", required=True, help="Version string (e.g., v1.17.1).")
    parser.add_argument("--dry-run", action="store_true", help="Skip writing reports (validation only).")
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    report_path = Path(args.ensemble_report)

    # ---- Dataset availability gate (V1.17.1 fix) ----
    if not dataset_path.exists():
        if args.dry_run:
            print(f"[dry-run] Dataset not found at {dataset_path}. Dry-run accepts this.")
            return
        print(
            f"ERROR: Dataset not found at {dataset_path}.\n"
            "A non-dry-run execution REQUIRES the dataset. "
            "Refusing to generate SKIPPED reports for a scientific release.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not report_path.exists():
        print(f"ERROR: Ensemble report not found at {report_path}.", file=sys.stderr)
        sys.exit(1)

    # ---- Load data ----
    print(f"Loading dataset from {dataset_path} ...")
    df = pd.read_parquet(dataset_path)
    print(f"  -> {len(df)} rows, {len(df.columns)} columns")

    with open(report_path, encoding="utf-8") as f:
        ensemble_report = json.load(f)

    out_dir = "reports/research" if not args.dry_run else "/tmp"
    v = args.version

    verdicts: dict[str, str] = {}

    print("Running Recent Window Analysis...")
    res = run_recent_window_analysis(df.copy(), ensemble_report, v, out_dir)
    verdicts["recent_window"] = res.get("verdict", "UNKNOWN")

    print("Running Regime Failure Analysis...")
    res = run_regime_analysis(df.copy(), v, out_dir)
    verdicts["regime_failure"] = res.get("verdict", "UNKNOWN")

    print("Running Cost Failure Analysis...")
    res = run_cost_analysis(df.copy(), v, out_dir)
    verdicts["cost_failure"] = res.get("verdict", "UNKNOWN")

    print("Running Feature Drift Analysis...")
    res = run_feature_drift_analysis(df.copy(), v, out_dir)
    verdicts["feature_drift"] = res.get("verdict", "UNKNOWN")

    print("Running Label Diagnostics...")
    res = run_label_diagnostics(df.copy(), v, out_dir)
    verdicts["label_diagnostics"] = res.get("verdict", "UNKNOWN")

    print("Running Horizon Diagnostics...")
    res = run_horizon_diagnostics(df.copy(), v, out_dir)
    verdicts["horizon_diagnostics"] = res.get("verdict", "UNKNOWN")

    print("Running Data Gap Analysis...")
    res = run_data_gap_analysis(df.copy(), v, out_dir)
    verdicts["data_gap_analysis"] = res.get("verdict", "UNKNOWN")

    print("Synthesizing Recommendation...")
    res = run_recommendation_engine(verdicts, v, out_dir)

    print("\n=== Final Verdicts ===")
    for k, vv in verdicts.items():
        print(f"  {k}: {vv}")
    print(f"\n  Primary Recommendation: {res.get('primary_recommendation')}")
    print(f"  Do Not Do Next: {res.get('do_not_do_next')}")


if __name__ == "__main__":
    main()
