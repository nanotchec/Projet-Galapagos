from __future__ import annotations

import argparse
import json
from pathlib import Path

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.data.public_trades.config import DEFAULT_1Y_WINDOW_END_V8_2, DEFAULT_1Y_WINDOW_START_V8_2
from galapagos.data.public_trades.one_year_window import (
    discover_public_trades_1y_window_v8_2,
    run_public_trades_1y_window_v8_2,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-network", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--start-date", default=DEFAULT_1Y_WINDOW_START_V8_2)
    parser.add_argument("--end-date", default=DEFAULT_1Y_WINDOW_END_V8_2)
    parser.add_argument("--allow-documented-gaps", action="store_true")
    parser.add_argument("--skip-project-state-check", action="store_true")
    args = parser.parse_args()
    if (
        args.start_date != DEFAULT_1Y_WINDOW_START_V8_2
        or args.end_date != DEFAULT_1Y_WINDOW_END_V8_2
        or args.allow_documented_gaps
    ):
        discover_public_trades_1y_window_v8_2(
            Path("."),
            start_date=args.start_date,
            end_date=args.end_date,
            allow_documented_gaps=args.allow_documented_gaps,
            no_network=args.no_network,
        )
    manifest = run_public_trades_1y_window_v8_2(
        Path("."),
        no_network=args.no_network,
        force=args.force,
        update_project_state=not args.skip_project_state_check,
    )
    summary = {
        "version": manifest["version"],
        "status": manifest["status"],
        "trade_source_type": manifest["source"]["trade_source_type"],
        "window_start": manifest["discovery"]["window_start"],
        "window_end": manifest["discovery"]["window_end"],
        "total_days": manifest["discovery"]["total_days"],
        "raw_files": len(manifest["raw_files"]),
        "partitions": len(manifest["outputs"]["partitions"]),
        "rows": manifest["outputs"]["total_rows"],
        "no_trading": manifest["safety"]["trading_enabled"] is False,
        "no_backtest": manifest["safety"]["backtest_enabled"] is False,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if manifest["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
