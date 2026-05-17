from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.ensemble.leakage_audit import audit_ensemble_leakage
from galapagos.research.report_models import write_research_report
from galapagos.utils.version import normalize_version


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit Ensemble Leakage")
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--version", default="v1.16.1")
    args = parser.parse_args()
    
    v_norm = normalize_version(args.version)

    if not Path(args.predictions).exists() or not Path(args.dataset).exists():
        print("Missing inputs.")
        return

    df_preds = pd.read_parquet(args.predictions)
    df_dataset = pd.read_parquet(args.dataset)
    
    # Run real audit
    res = audit_ensemble_leakage(df_dataset, df_preds)
    
    write_research_report(
        name=f"ensemble_leakage_audit_{v_norm}",
        payload=res,
        title=f"Ensemble Leakage Audit {v_norm.upper()}",
        lines=[
            f"Verdict: {res['status']}.",
            f"Rows audited: {res['rows_audited']}.",
            f"Checks performed: {len(res['checks'])}.",
        ] + [f"- {c}" for c in res['checks']],
        output_dir="reports/research"
    )
    
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
