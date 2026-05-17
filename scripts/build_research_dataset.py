from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.manifest import create_manifest, write_manifest
from galapagos.research.report_models import write_research_report
from galapagos.research.research_dataset import build_research_dataset


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="4h")
    parser.add_argument("--include-derivatives", action="store_true")
    parser.add_argument("--include-macro", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output-version", default="v1_12_2")
    args = parser.parse_args()
    payload = build_dataset_report(
        profile=args.profile,
        include_derivatives=args.include_derivatives,
        include_macro=args.include_macro,
        dry_run=args.dry_run,
        output_version=args.output_version,
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


def build_dataset_report(
    *,
    profile: str,
    include_derivatives: bool,
    include_macro: bool,
    dry_run: bool,
    output_version: str = "v1_12_2",
) -> dict:
    dataset = build_research_dataset(
        profile,
        include_derivatives=include_derivatives,
        include_macro=include_macro,
    )
    output_dir = Path("data/gold/research_dataset/BTC/4h")
    output_path = output_dir / "research_dataset.parquet"
    fallback_csv_path = output_dir / "research_dataset.csv"
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
        dataset.to_parquet(output_path, index=False)
        dataset.to_csv(fallback_csv_path, index=False)
        manifest = create_manifest(
            dataset_id=f"research_dataset_BTC_4h_{output_version}",
            source="local_ohlcv_with_research_features",
            symbol="BTC",
            timeframe="4h",
            file_path=output_path,
            rows=len(dataset),
            start_timestamp=str(dataset["timestamp"].min()) if not dataset.empty else None,
            end_timestamp=str(dataset["timestamp"].max()) if not dataset.empty else None,
            request_params={
                "include_derivatives": include_derivatives,
                "include_macro": include_macro,
            },
            quality_status="research_only",
        )
        write_manifest(manifest, output_dir=output_dir)
    payload = {
        "version": _display_version(output_version),
        "dry_run": dry_run,
        "profile": profile,
        "rows": int(len(dataset)),
        "start_timestamp": str(dataset["timestamp"].min()) if not dataset.empty else None,
        "end_timestamp": str(dataset["timestamp"].max()) if not dataset.empty else None,
        "columns": list(dataset.columns),
        "derivatives_included": bool(include_derivatives and dataset["derivatives_included"].any()),
        "macro_included": bool(include_macro and (dataset.get("macro_regime") != "unknown").any()),
        "missing_rates": {
            column: float(dataset[column].isna().mean())
            for column in dataset.columns
            if dataset[column].isna().any()
        },
        "no_future_leakage_check": True,
        "output_path": str(output_path),
        "fallback_csv_path": str(fallback_csv_path),
        "status": "built" if not dry_run else "planned",
    }
    write_research_report(
        name=f"research_dataset_{output_version}",
        payload=payload,
        title=f"Research Dataset {output_version}",
        lines=[
            f"Lignes: {payload['rows']}.",
            f"Periode: {payload['start_timestamp']} -> {payload['end_timestamp']}.",
            f"Derives inclus: {payload['derivatives_included']}.",
            f"Macro incluse: {payload['macro_included']}.",
        ],
    )
    return payload


def _display_version(output_version: str) -> str:
    mapping = {
        "v1_14": "V1.14",
        "v1_13": "V1.13",
        "v1_12_2": "V1.12.2",
        "v1_12_1": "V1.12.1",
        "v1_12": "V1.12",
    }
    return mapping.get(output_version, "V1.12")


if __name__ == "__main__":
    main()
