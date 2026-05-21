from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.data.public_market.config import PublicMarketIngestionConfig
from galapagos.data.public_market.ingestion import run_public_market_ingestion


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--market-type", required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--timeframe", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--no-network", action="store_true")
    parser.add_argument("--output-root", default=".")
    parser.add_argument("--fail-on-quality-warning", action="store_true")
    args = parser.parse_args()
    config = PublicMarketIngestionConfig(
        source=args.source,
        market_type=args.market_type,
        symbol=args.symbol,
        timeframe=args.timeframe,
        date=args.date,
        output_root=Path(args.output_root),
        force=args.force,
        no_network=args.no_network,
        fail_on_quality_warning=args.fail_on_quality_warning,
    )
    try:
        manifest = run_public_market_ingestion(config)
    except Exception as exc:
        print(f"V2.3 public market ingestion failed: {exc}", file=sys.stderr)
        raise
    summary = {
        "version": manifest["version"],
        "status": manifest["status"],
        "network_used": manifest["network_used"],
        "raw_path": manifest["raw"]["path"],
        "silver_path": manifest["silver"]["path"],
        "rows": manifest["quality"]["rows"],
        "expected_rows": manifest["quality"]["expected_rows"],
        "gap_count": manifest["quality"]["gap_count"],
        "duplicate_rows": manifest["quality"]["duplicate_rows"],
        "ohlc_violations": manifest["quality"]["ohlc_violations"],
        "trading_enabled": manifest["trading_enabled"],
        "paper_live_enabled": manifest["paper_live_enabled"],
        "ml_enabled": manifest["ml_enabled"],
        "labels_enabled": manifest["labels_enabled"],
        "backtest_enabled": manifest["backtest_enabled"],
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
