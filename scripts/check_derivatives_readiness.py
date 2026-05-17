from __future__ import annotations

import argparse
import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.derivatives_readiness import build_derivatives_readiness
from galapagos.research.report_models import write_research_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    payload = build_derivatives_readiness(args.symbol, dry_run=args.dry_run)
    write_research_report(
        name="derivatives_readiness_v1_11",
        payload=payload,
        title="Derivatives Readiness V1.11",
        lines=[
            "Readiness des donnees derivees sans secret affiche.",
            "Les endpoints publics restent optionnels; CoinGlass/FRED demandent une cle.",
        ],
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
