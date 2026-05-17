from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

import pandas as pd

from galapagos.data.macro.macro_features import build_macro_features
from galapagos.research.report_models import write_research_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeframe", default="4h")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    records = _load_fred_records()
    features = build_macro_features(records, timeframe=args.timeframe)
    output_dir = Path("data/gold/macro_features") / args.timeframe
    output_path = output_dir / "macro_features.csv"
    if not args.dry_run and not features.empty:
        output_dir.mkdir(parents=True, exist_ok=True)
        features.to_csv(output_path, index=False)
    payload = {
        "version": "V1.12.2",
        "dry_run": args.dry_run,
        "rows": int(len(features)),
        "status": "unavailable" if features.empty else "available",
        "macro_included": not features.empty,
        "input_rows": int(len(records)),
        "output_path": str(output_path),
    }
    write_research_report(
        name="fred_macro_readiness_v1_12_2",
        payload={**payload, "fred_api_key": "configured_or_missing_not_logged"},
        title="FRED Macro Readiness V1.12.2",
        lines=[
            f"Macro features construites: {payload['macro_included']}.",
            f"Lignes features: {payload['rows']}.",
            "Aucun secret affiche.",
        ],
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _load_fred_records() -> pd.DataFrame:
    base = Path("data/silver/macro/fred")
    frames = []
    if base.exists():
        for path in sorted(base.glob("*.csv")):
            try:
                frames.append(pd.read_csv(path))
            except Exception:
                continue
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


if __name__ == "__main__":
    main()
