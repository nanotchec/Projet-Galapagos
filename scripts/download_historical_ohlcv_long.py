from __future__ import annotations

import argparse
import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.ccxt_historical import plan_ccxt_ohlcv_fetch


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exchange", required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--timeframe", default="4h")
    parser.add_argument("--years", type=int, default=3)
    parser.add_argument("--max-pages", type=int, default=1000)
    parser.add_argument("--dry-run", action="store_true", default=True)
    args = parser.parse_args()
    plan = plan_ccxt_ohlcv_fetch(
        exchange=args.exchange,
        symbol=args.symbol,
        timeframe=args.timeframe,
        years=args.years,
        max_pages=args.max_pages,
        dry_run=True,
    )
    print(json.dumps({"version": "V1.12", "plan": plan.to_dict()}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
