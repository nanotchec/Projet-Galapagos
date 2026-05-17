from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.binance_public_archive import plan_binance_ohlcv_download


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--market", default="futures_um")
    parser.add_argument("--interval", default="4h")
    parser.add_argument("--years", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    plans = plan_binance_ohlcv_download(
        symbol=args.symbol,
        market=args.market,
        interval=args.interval,
        years=args.years,
    )
    payload = {
        "version": "V1.12",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "dry_run": args.dry_run,
        "symbol": args.symbol,
        "market": args.market,
        "interval": args.interval,
        "planned_files": len(plans),
        "existing_files": sum(1 for plan in plans if plan.exists),
        "status": "planned",
        "plans_preview": [plan.to_dict() for plan in plans[:5]],
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
