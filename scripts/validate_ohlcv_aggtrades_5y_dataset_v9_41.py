from __future__ import annotations

import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.datasets.ohlcv_aggtrades_5y_dataset_v9_41_validation import validate_v9_41_report


def main() -> int:
    result = validate_v9_41_report()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
