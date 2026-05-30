from __future__ import annotations

import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.labels.ohlcv_aggtrades_5y_label_factory_v9_40_validation import validate_v9_40_report


def main() -> int:
    result = validate_v9_40_report()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
