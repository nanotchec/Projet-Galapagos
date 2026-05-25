from __future__ import annotations

import argparse
import json
from pathlib import Path

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.data.public_trades.ingestion import run_public_trades_ingestion_v7_0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-network", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--skip-project-state-check", action="store_true")
    args = parser.parse_args()
    print("=== Generating Galapagos V7.0 Public Trades Historical Ingestion Preview ===")
    print("V7.0 run mode: data-only, no features, no labels, no ML, no backtest.")
    manifest = run_public_trades_ingestion_v7_0(
        Path("."),
        no_network=args.no_network,
        force=args.force,
        update_project_state=True,
    )
    print(f"Status: {manifest['status']}")
    print(f"Ingestion run id: {manifest['ingestion_run_id']}")
    print(f"Window: {manifest['discovery']['window_start']} -> {manifest['discovery']['window_end']}")
    print(f"Rows: {manifest['outputs']['rows']}")
    print(json.dumps({"version": manifest["version"], "status": manifest["status"]}, ensure_ascii=False))
    if manifest["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
