from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.datasets.ohlcv_trades_window import run_ohlcv_trades_offline_supervised_dataset_v7_3
from galapagos.datasets.schemas import TIMEFRAMES_V7_3


def main() -> None:
    print("=== Generating Galapagos V7.3 OHLCV + Public Trades Offline Supervised Dataset ===")
    print("V7.3 run mode: validate_inputs=True")
    print("Only validate_ohlcv_trades_feature_store_v7_2 and validate_max_history_label_factory_v5_2 are called before dataset generation.")
    manifest = run_ohlcv_trades_offline_supervised_dataset_v7_3(Path("."))
    summary = {
        "version": manifest["version"],
        "status": manifest["status"],
        "dataset_run_id": manifest["dataset_run_id"],
        "window_start": manifest["input_features_manifest"]["window_start"],
        "window_end": manifest["input_features_manifest"]["window_end"],
        "total_days": manifest["input_features_manifest"]["total_days"],
        "dataset_columns": len(manifest["dataset_columns"]),
        "feature_columns_count": manifest["feature_columns_count"],
        "outputs": {timeframe: manifest["outputs"][timeframe] for timeframe in TIMEFRAMES_V7_3},
        "splits": {timeframe: manifest["splits"][timeframe] for timeframe in TIMEFRAMES_V7_3},
        "no_trading": manifest["safety"]["trading_enabled"] is False,
        "no_backtest": manifest["safety"]["backtest_enabled"] is False,
        "no_ml": manifest["safety"]["ml_enabled"] is False,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if manifest["status"] != "PASS":
        raise SystemExit(1)
    print("================================================================================")


if __name__ == "__main__":
    main()
