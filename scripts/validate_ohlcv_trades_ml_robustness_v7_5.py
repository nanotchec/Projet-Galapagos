from __future__ import annotations

import json
from pathlib import Path

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.ml.ohlcv_trades_robustness_validation import validate_ohlcv_trades_ml_robustness_v7_5


def main() -> None:
    result = validate_ohlcv_trades_ml_robustness_v7_5(Path("."))
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
