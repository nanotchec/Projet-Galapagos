from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

import pandas as pd

from galapagos.research.alpha_score_quality import analyze_alpha_score_quality
from galapagos.research.report_models import write_research_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    args = parser.parse_args()
    dataset_path = Path(args.dataset)
    dataset = (
        pd.read_parquet(dataset_path)
        if dataset_path.suffix == ".parquet"
        else pd.read_csv(dataset_path)
    )
    payload = analyze_alpha_score_quality(dataset)
    payload |= {
        "dataset": str(dataset_path),
        "codex_cli_called": False,
        "holdout_executed": False,
    }
    write_research_report(
        name="alpha_score_quality_v1_14",
        payload=payload,
        title="Alpha Score Quality V1.14",
        lines=[
            f"Verdict: {payload['verdict']}.",
            f"Lignes: {payload['rows']}.",
            "Analyse offline: correlation, buckets, regimes, couts.",
        ],
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
