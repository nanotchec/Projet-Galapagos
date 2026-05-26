from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.datasets.refined_ohlcv_trades_window_validation import validate_refined_ohlcv_trades_offline_supervised_dataset_v9_1


def main() -> int:
    result = validate_refined_ohlcv_trades_offline_supervised_dataset_v9_1(Path("."))
    printable = {key: value for key, value in result.items() if key != "manifest"}
    print(json.dumps(printable, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
