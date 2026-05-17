from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

import pandas as pd

from galapagos.research.alpha_scoring import build_alpha_scores, score_report
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
    scored = build_alpha_scores(dataset)
    output = dataset_path.with_name("research_dataset_with_alpha_scores.parquet")
    output_csv = dataset_path.with_name("research_dataset_with_alpha_scores.csv")
    scored.to_parquet(output, index=False)
    scored.to_csv(output_csv, index=False)
    payload = score_report(scored)
    payload |= {
        "dataset": str(dataset_path),
        "output_path": str(output),
        "output_csv": str(output_csv),
        "codex_cli_called": False,
        "holdout_executed": False,
    }
    write_research_report(
        name="alpha_scores_v1_14",
        payload=payload,
        title="Alpha Scores V1.14",
        lines=[
            f"Lignes scorees: {payload['rows']}.",
            "Score research-only: aucune regle de trading modifiee.",
            f"Formule: {payload['formula']}.",
        ],
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
