from __future__ import annotations

import argparse
import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.backtest.historical_data import cache_kraken_ohlcv
from galapagos.utils.config_loader import load_profile


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--profile",
        required=True,
        choices=["30m", "4h", "galapagos_30m", "galapagos_4h"],
    )
    parser.add_argument("--days", type=int, required=True)
    args = parser.parse_args()
    profile = load_profile(args.profile)
    result = cache_kraken_ohlcv(
        symbol=profile["symbol"],
        timeframe=profile["timeframe"],
        days=args.days,
    )
    print(json.dumps(result.metadata, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
