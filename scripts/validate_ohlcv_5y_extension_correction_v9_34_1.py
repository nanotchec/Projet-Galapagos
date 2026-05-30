from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.ohlcv_5y_extension_correction_v9_34_1_validation import validate_v9_34_1_report  # noqa: E402


def main() -> int:
    result = validate_v9_34_1_report(Path("."))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
