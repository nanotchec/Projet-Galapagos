from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.datasets.ohlcv_trades_90d_window_validation import validate_ohlcv_trades_90d_offline_supervised_dataset_v7_9


def main() -> None:
    result = validate_ohlcv_trades_90d_offline_supervised_dataset_v7_9(Path("."))
    printable = {key: value for key, value in result.items() if key != "manifest"}
    print(json.dumps(printable, indent=2, ensure_ascii=False, default=str))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
