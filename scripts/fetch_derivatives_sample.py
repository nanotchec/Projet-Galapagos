from __future__ import annotations

import argparse
import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.derivatives_readiness import fetch_public_derivatives_sample


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["binance", "bybit"], required=True)
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.dry_run:
        payload = {
            "source": args.source,
            "symbol": args.symbol,
            "limit": args.limit,
            "dry_run": True,
            "network_called": False,
            "status": "not_called",
        }
    else:
        payload = fetch_public_derivatives_sample(
            source=args.source,
            symbol=args.symbol,
            limit=args.limit,
        )
        payload["dry_run"] = False
        payload["network_called"] = True
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
