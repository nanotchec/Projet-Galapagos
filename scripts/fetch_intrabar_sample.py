"""Script to fetch intrabar data samples."""
from __future__ import annotations

import argparse

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.intrabar.downloader import download_intrabar_sample
from galapagos.research.intrabar.report import write_intrabar_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=str, required=True)
    parser.add_argument("--symbol", type=str, required=True)
    parser.add_argument("--timeframe", type=str, required=True)
    parser.add_argument("--days", type=int, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = download_intrabar_sample(
        args.source, args.symbol, args.timeframe, args.days, dry_run=args.dry_run
    )

    verdict = "INTRABAR_SAMPLE_FETCH_SUCCESS"
    if result["status"] == "failed":
        verdict = "INTRABAR_SAMPLE_FETCH_FAILED"
    elif result["status"] == "dry_run":
        verdict = "INTRABAR_SAMPLE_DRY_RUN"

    payload = {
        "verdict": verdict,
        "request": {
            "source": args.source,
            "symbol": args.symbol,
            "timeframe": args.timeframe,
            "requested_days": args.days,
            "dry_run": args.dry_run,
        },
        "result": result,
    }

    lines = [
        f"Verdict: **{verdict}**",
        "",
        f"- Fetched {result.get('rows', 0)} rows.",
        f"- Path: {result.get('file_path')}",
    ]

    write_intrabar_report(
        "intrabar_download_v1_18",
        payload,
        "Intrabar Download Sample V1.18",
        lines,
    )

    print(f"Download complete. Verdict: {verdict}. Rows: {result.get('rows', 0)}")


if __name__ == "__main__":
    main()
