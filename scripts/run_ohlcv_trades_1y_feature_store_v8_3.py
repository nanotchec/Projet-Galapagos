from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.features.ohlcv_trades_1y import TIMEFRAMES_V8_3, run_ohlcv_trades_1y_feature_store_v8_3


def main() -> None:
    print("=== Generating Galapagos V8.3 OHLCV + Public Trades Feature Store ===")
    print("V8.3 run mode: validate_inputs=True")
    print("Only validate_max_history_public_market_data_v5_0 and validate_public_trades_1y_window_v8_2 are called before feature generation.")
    manifest = run_ohlcv_trades_1y_feature_store_v8_3(Path("."))
    summary = {
        "version": manifest["version"],
        "status": manifest["status"],
        "feature_run_id": manifest["feature_run_id"],
        "window_start": manifest["window"]["window_start"],
        "window_end": manifest["window"]["window_end"],
        "total_days": manifest["window"]["total_days"],
        "feature_columns": len(manifest["feature_columns"]),
        "trade_source_type": manifest["input_trades_manifest"]["trade_source_type"],
        "outputs": {timeframe: manifest["outputs"][timeframe] for timeframe in TIMEFRAMES_V8_3},
        "no_trading": manifest["safety"]["trading_enabled"] is False,
        "no_backtest": manifest["safety"]["backtest_enabled"] is False,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if manifest["status"] != "PASS":
        raise SystemExit(1)
    print("======================================================================")


if __name__ == "__main__":
    main()
