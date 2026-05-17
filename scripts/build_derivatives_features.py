from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

import pandas as pd

from galapagos.data.derivatives.features import build_derivatives_features
from galapagos.data.manifest import create_manifest, write_manifest
from galapagos.research.report_models import write_research_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--timeframe", default="4h")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    base = Path("data/silver/derivatives")
    frames = []
    for path in base.glob(f"*/{args.symbol}/*.csv") if base.exists() else []:
        frames.append(pd.read_csv(path))
    records = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    features = build_derivatives_features(records, timeframe=args.timeframe)
    output = Path("data/gold/derivatives_features") / args.symbol / args.timeframe
    if not args.dry_run and not features.empty:
        output.mkdir(parents=True, exist_ok=True)
        output_path = output / "derivatives_features.csv"
        features.to_csv(output_path, index=False)
        manifest = create_manifest(
            dataset_id=f"derivatives_features_{args.symbol}_{args.timeframe}_v1_14",
            source="public_derivatives_silver",
            symbol=args.symbol,
            timeframe=args.timeframe,
            file_path=output_path,
            rows=len(features),
            request_params={"symbol": args.symbol, "timeframe": args.timeframe},
            quality_status="research_only",
        )
        write_manifest(manifest)
    payload = {
        "version": "V1.14",
        "dry_run": args.dry_run,
        "rows": int(len(features)),
        "output_dir": str(output),
        "status": "unavailable" if features.empty else "available",
        "columns": list(features.columns),
        "missing_rates": {
            column: float(features[column].isna().mean())
            for column in features.columns
            if features[column].isna().any()
        } if not features.empty else {},
    }
    write_research_report(
        name="derivatives_features_v1_14",
        payload=payload,
        title="Derivatives Features V1.14",
        lines=[
            f"Status: {payload['status']}.",
            f"Lignes: {payload['rows']}.",
            "Features causales construites sans donnees futures.",
        ],
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
