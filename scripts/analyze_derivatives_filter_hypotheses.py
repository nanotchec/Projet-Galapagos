from __future__ import annotations

import argparse
import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

import pandas as pd

from galapagos.research.derivatives_signal_quality import analyze_filter_hypotheses
from galapagos.research.report_models import write_research_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    args = parser.parse_args()
    dataset = (
        pd.read_parquet(args.dataset)
        if args.dataset.endswith(".parquet")
        else pd.read_csv(args.dataset)
    )
    payload = analyze_filter_hypotheses(dataset)
    payload["dataset"] = args.dataset
    payload["codex_cli_called"] = False
    payload["holdout_executed"] = False
    write_research_report(
        name="derivatives_filter_hypotheses_v1_14",
        payload=payload,
        title="Derivatives Filter Hypotheses V1.14",
        lines=[
            f"Verdict: {payload['verdict']}.",
            "Hypotheses offline uniquement; aucune regle trading modifiee.",
        ],
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
