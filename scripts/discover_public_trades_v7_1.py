from __future__ import annotations

import argparse
import json
from pathlib import Path

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.data.public_trades.config import DEFAULT_EXPANDED_WINDOW_END_V7_1, DEFAULT_EXPANDED_WINDOW_START_V7_1
from galapagos.data.public_trades.expanded_window import discover_public_trades_expanded_window_v7_1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-date", default=DEFAULT_EXPANDED_WINDOW_START_V7_1)
    parser.add_argument("--end-date", default=DEFAULT_EXPANDED_WINDOW_END_V7_1)
    parser.add_argument("--allow-documented-gaps", action="store_true")
    parser.add_argument("--no-network", action="store_true")
    args = parser.parse_args()
    result = discover_public_trades_expanded_window_v7_1(
        Path("."),
        start_date=args.start_date,
        end_date=args.end_date,
        allow_documented_gaps=args.allow_documented_gaps,
        no_network=args.no_network,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
