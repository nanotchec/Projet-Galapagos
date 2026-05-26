from __future__ import annotations

import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.ml.refined_strict_walk_forward import run_refined_strict_walk_forward_validation_v9_3


def main() -> int:
    manifest = run_refined_strict_walk_forward_validation_v9_3()
    print(
        json.dumps(
            {
                "version": manifest["version"],
                "status": manifest["status"],
                "target_name": manifest["target_name"],
                "feature_columns_count": manifest["feature_columns_count"],
                "folds_count": {timeframe: len(payload) for timeframe, payload in manifest["folds"].items()},
                "score_rows": {timeframe: payload["rows"] for timeframe, payload in manifest["outputs"]["scores"].items()},
                "no_backtest": not manifest["safety"]["backtest_enabled"],
                "no_strategy": not manifest["safety"]["strategy_enabled"],
                "no_orders": not manifest["safety"]["orders_enabled"],
                "no_trading": not manifest["safety"]["trading_enabled"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if manifest["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
