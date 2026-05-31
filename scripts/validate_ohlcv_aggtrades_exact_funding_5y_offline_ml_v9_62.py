from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.ml.ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62_validation import validate_offline_ml_v9_62


def main() -> int:
    errors = validate_offline_ml_v9_62(Path("."))
    payload = {"version": "V9.62", "status": "PASS" if not errors else "FAIL", "passed": not errors, "errors": errors}
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
