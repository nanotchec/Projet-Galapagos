from __future__ import annotations

import argparse
import json
from pathlib import Path

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.data.public_market.max_history_window import run_max_history_public_market_data_v5_0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--no-network", action="store_true")
    parser.add_argument("--skip-project-state-check", action="store_true")
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--allow-documented-gaps", action="store_true")
    args = parser.parse_args()
    print("=== Generating Galapagos V5.0 Max Historical Public Market Data Expansion ===")
    print("V5.0 run mode: data-only, no features, no labels, no ML, no backtest.")
    manifest = run_max_history_public_market_data_v5_0(
        Path("."),
        force=args.force,
        no_network=args.no_network,
        validate_project_state=not args.skip_project_state_check,
        start_date=args.start_date,
        end_date=args.end_date,
        allow_documented_gaps=args.allow_documented_gaps,
    )
    print(f"Status: {manifest['status']}")
    print(f"Run id: {manifest['run_id']}")
    print(f"Window: {manifest['discovery']['window_start']} -> {manifest['discovery']['window_end']}")
    print(f"Rows: {json.dumps(manifest['expected_rows'], sort_keys=True)}")
    print(json.dumps({"version": manifest["version"], "status": manifest["status"]}, ensure_ascii=False))
    if manifest["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
