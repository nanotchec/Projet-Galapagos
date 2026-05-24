from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.datasets.advanced_ohlcv_window_validation import validate_advanced_ohlcv_offline_supervised_dataset_v6_1


def main() -> None:
    result = validate_advanced_ohlcv_offline_supervised_dataset_v6_1(Path("."))
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
