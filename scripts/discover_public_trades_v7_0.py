from __future__ import annotations

import argparse
import json
from pathlib import Path

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.data.public_trades.discovery import discover_public_trades_v7_0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview-days", type=int, default=1)
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--allow-documented-gaps", action="store_true")
    parser.add_argument("--no-download", action="store_true")
    args = parser.parse_args()
    print("=== Discovering Galapagos V7.0 Public Trades Historical Preview ===")
    print("V7.0 discovery mode: public read-only, no features, no labels, no ML, no backtest.")
    discovery = discover_public_trades_v7_0(
        Path("."),
        preview_days=args.preview_days,
        start_date=args.start_date,
        end_date=args.end_date,
        allow_documented_gaps=args.allow_documented_gaps,
        download_raw=not args.no_download,
    )
    window = discovery["recommended_window"]
    print(f"Status: {discovery['status']}")
    print(f"Source: {discovery['source_type']}")
    print(f"Window: {window['window_start']} -> {window['window_end']}")
    print(f"Available dates: {discovery['total_available_days']}")
    print(json.dumps({"version": discovery["version"], "status": discovery["status"]}, ensure_ascii=False))
    if discovery["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
