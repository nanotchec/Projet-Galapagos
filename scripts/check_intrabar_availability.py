"""Script to check availability of intrabar data."""
from __future__ import annotations

import argparse

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.intrabar.availability import check_availability
from galapagos.research.intrabar.report import write_intrabar_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", type=str, required=True)
    parser.add_argument("--sources", type=str, required=True)
    parser.add_argument("--timeframes", type=str, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    sources = [s.strip() for s in args.sources.split(",")]
    timeframes = [t.strip() for t in args.timeframes.split(",")]

    results = check_availability(sources, args.symbol, timeframes, dry_run=args.dry_run)

    # Determine overall verdict
    verdict = "INTRABAR_UNAVAILABLE"
    has_5m_public = any(r["status"] == "available" and r["timeframe"] == "5m" for r in results)
    has_1m_public = any(r["status"] == "available" and r["timeframe"] == "1m" for r in results)

    if args.dry_run:
        verdict = "INTRABAR_DRY_RUN_MOCKED"
    elif has_1m_public:
        verdict = "INTRABAR_1M_PUBLIC_AVAILABLE"
    elif has_5m_public:
        verdict = "INTRABAR_5M_PUBLIC_AVAILABLE"

    payload = {
        "symbol": args.symbol,
        "sources_checked": sources,
        "timeframes_checked": timeframes,
        "dry_run": args.dry_run,
        "verdict": verdict,
        "results": results,
    }

    lines = [f"Verdict: **{verdict}**", ""]
    for r in results:
        lines.append(f"- **{r['source']} {r['timeframe']}**: {r['status']}")
        lines.append(f"  - Notes: {r['notes']}")

    write_intrabar_report(
        "intrabar_availability_v1_18",
        payload,
        "Intrabar Availability V1.18",
        lines,
    )

    print(f"Availability check complete. Verdict: {verdict}")


if __name__ == "__main__":
    main()
