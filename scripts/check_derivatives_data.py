from __future__ import annotations

import argparse
import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.binance_futures_collector import BinanceFuturesCollector
from galapagos.reports.derivatives_quality_report import generate_derivatives_quality_report
from galapagos.utils.paths import project_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="BTC/USDT:USDT")
    args = parser.parse_args()
    snapshot = BinanceFuturesCollector().fetch_derivatives_snapshot(args.symbol)
    paths = generate_derivatives_quality_report(snapshot, project_path("reports/diagnostics"))
    print(
        json.dumps(
            {"snapshot": snapshot, "paths": {k: str(v) for k, v in paths.items()}},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
