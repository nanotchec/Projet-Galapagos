from __future__ import annotations

import json

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.features.refined_ohlcv_trades_validation import validate_refined_ohlcv_trades_feature_store_v9_0


def main() -> None:
    result = validate_refined_ohlcv_trades_feature_store_v9_0()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
