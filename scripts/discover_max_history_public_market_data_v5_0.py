from __future__ import annotations

import argparse
import json
from pathlib import Path

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.data.public_market.max_history_discovery import discover_max_history_public_market_data_v5_0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-network", action="store_true")
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--allow-documented-gaps", action="store_true")
    args = parser.parse_args()
    print("=== Discovering Galapagos V5.0 Max Historical Public Market Data Window ===")
    print("V5.0 discovery mode: public read-only OHLCV only, no features, no labels, no ML, no backtest.")
    discovery = discover_max_history_public_market_data_v5_0(
        Path("."),
        no_network=args.no_network,
        start_date=args.start_date,
        end_date=args.end_date,
        allow_documented_gaps=args.allow_documented_gaps,
    )
    print(f"Status: {discovery['status']}")
    print(f"Window: {discovery['window_start']} -> {discovery['window_end']}")
    print(f"Total days: {discovery['total_days']}")
    print(json.dumps({"version": discovery["version"], "status": discovery["status"]}, ensure_ascii=False))
    if discovery["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
