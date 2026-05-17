from __future__ import annotations

import argparse
import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.derivatives.coverage import (
    audit_derivatives_coverage,
    audit_derivatives_coverage_expansion,
    derivatives_data_quality,
)
from galapagos.research.report_models import write_research_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--timeframe", default="4h")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    payload = audit_derivatives_coverage(args.symbol, args.timeframe, dry_run=args.dry_run)
    expansion = audit_derivatives_coverage_expansion(
        args.symbol,
        args.timeframe,
        dry_run=args.dry_run,
    )
    quality = derivatives_data_quality(args.symbol, args.timeframe)
    if not args.dry_run:
        write_research_report(
            name="derivatives_coverage_v1_14",
            payload=payload,
            title="Derivatives Coverage V1.14",
            lines=[
                f"Symbol: {args.symbol}.",
                f"Timeframe: {args.timeframe}.",
                f"Verdict: {payload['verdict']}.",
                "CoinGlass reste optionnel et non utilise sans cle.",
            ],
        )
        write_research_report(
            name="derivatives_coverage_expansion_v1_14",
            payload=expansion,
            title="Derivatives Coverage Expansion V1.14",
            lines=[
                f"Symbol: {args.symbol}.",
                f"Timeframe: {args.timeframe}.",
                f"Verdicts: {', '.join(expansion['verdicts'])}.",
                "Audit des donnees publiques collectees, collectables, limitees ou payantes.",
            ],
        )
        write_research_report(
            name="derivatives_data_quality_v1_14",
            payload=quality,
            title="Derivatives Data Quality V1.14",
            lines=[
                f"Verdict: {quality['verdict']}.",
                f"Lignes features: {quality['features_rows']}.",
                "Rapport de sparsity, alignement et limites connues.",
            ],
        )
    output_payload = expansion if args.dry_run else payload
    print(json.dumps(output_payload, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
