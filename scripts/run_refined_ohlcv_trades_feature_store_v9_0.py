from __future__ import annotations

import json

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.features.refined_ohlcv_trades import run_refined_ohlcv_trades_feature_store_v9_0


def main() -> None:
    manifest = run_refined_ohlcv_trades_feature_store_v9_0()
    print(
        json.dumps(
            {
                "version": manifest["version"],
                "status": manifest["status"],
                "selected_features_count": manifest["selected_features_count"],
                "outputs": {timeframe: payload["rows"] for timeframe, payload in manifest["outputs"].items()},
                "no_labels": True,
                "no_dataset": True,
                "no_ml": True,
                "no_backtest": True,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
