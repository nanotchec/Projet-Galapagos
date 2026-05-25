from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.features.ohlcv_trades_90d import TIMEFRAMES_V7_8, run_ohlcv_trades_90d_feature_store_v7_8


def main() -> None:
    print("=== Generating Galapagos V7.8 OHLCV + Public Trades Feature Store ===")
    print("V7.8 run mode: validate_inputs=True")
    print("Only validate_max_history_public_market_data_v5_0 and validate_public_trades_90d_window_v7_7 are called before feature generation.")
    manifest = run_ohlcv_trades_90d_feature_store_v7_8(Path("."))
    summary = {
        "version": manifest["version"],
        "status": manifest["status"],
        "feature_run_id": manifest["feature_run_id"],
        "window_start": manifest["window"]["window_start"],
        "window_end": manifest["window"]["window_end"],
        "total_days": manifest["window"]["total_days"],
        "feature_columns": len(manifest["feature_columns"]),
        "trade_source_type": manifest["input_trades_manifest"]["trade_source_type"],
        "outputs": {timeframe: manifest["outputs"][timeframe] for timeframe in TIMEFRAMES_V7_8},
        "no_trading": manifest["safety"]["trading_enabled"] is False,
        "no_backtest": manifest["safety"]["backtest_enabled"] is False,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if manifest["status"] != "PASS":
        raise SystemExit(1)
    print("======================================================================")


if __name__ == "__main__":
    main()
