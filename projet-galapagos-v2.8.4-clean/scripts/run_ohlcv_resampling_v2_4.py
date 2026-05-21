from __future__ import annotations

import json
import sys
from pathlib import Path

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.validation.resampling import run_ohlcv_resampling_v2_4


def main() -> None:
    try:
        manifest = run_ohlcv_resampling_v2_4(Path("."))
    except Exception as exc:
        print(f"V2.4 OHLCV resampling failed: {exc}", file=sys.stderr)
        raise
    summary = {
        "version": manifest["version"],
        "status": manifest["status"],
        "input_rows": manifest["input_1m"]["rows"],
        "output_rows": {timeframe: block["rows"] for timeframe, block in manifest["outputs"].items()},
        "parent_child_consistency": manifest["parent_child_consistency"],
        "trading_enabled": manifest["trading_enabled"],
        "paper_live_enabled": manifest["paper_live_enabled"],
        "ml_enabled": manifest["ml_enabled"],
        "labels_enabled": manifest["labels_enabled"],
        "backtest_enabled": manifest["backtest_enabled"],
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
