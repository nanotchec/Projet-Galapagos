from __future__ import annotations

import argparse
import json
from pathlib import Path

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.data.public_market.expanded_window import run_expanded_public_market_data_v3_5


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--no-network", action="store_true")
    parser.add_argument("--skip-project-state-check", action="store_true")
    args = parser.parse_args()
    print("=== Generating Galapagos V3.5 90-Day Public Market Data Expansion ===")
    print("V3.5 run mode: data-only, no features, no labels, no ML, no backtest.")
    manifest = run_expanded_public_market_data_v3_5(
        Path("."),
        force=args.force,
        no_network=args.no_network,
        validate_project_state=not args.skip_project_state_check,
    )
    print(f"Status: {manifest['status']}")
    print(f"Run id: {manifest['run_id']}")
    print(f"Rows: {json.dumps(manifest['expected_rows'], sort_keys=True)}")
    print(json.dumps({"version": manifest["version"], "status": manifest["status"]}, ensure_ascii=False))
    if manifest["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
