from __future__ import annotations

import argparse
import json
from pathlib import Path

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.data.public_market.multi_day import run_multi_day_public_market_data_v2_9


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--no-network", action="store_true")
    args = parser.parse_args()
    manifest = run_multi_day_public_market_data_v2_9(
        Path(args.root),
        force=args.force,
        no_network=args.no_network,
    )
    print("=== Galapagos V2.9 Multi-Day Public Market Data ===")
    print(f"Status: {manifest['status']}")
    print(f"Run id: {manifest['run_id']}")
    for timeframe, output in manifest["outputs"].items():
        print(f"{timeframe}: rows={output['rows']} sha256={output['sha256']}")


if __name__ == "__main__":
    main()
