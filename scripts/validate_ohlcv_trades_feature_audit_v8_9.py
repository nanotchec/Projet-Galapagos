from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.features.ohlcv_trades_feature_audit_validation import validate_ohlcv_trades_feature_audit_v8_9


def main() -> None:
    result = validate_ohlcv_trades_feature_audit_v8_9(Path("."))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
