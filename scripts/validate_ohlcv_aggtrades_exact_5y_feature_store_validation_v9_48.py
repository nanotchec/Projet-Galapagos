from __future__ import annotations

import argparse
import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.features.ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48_validation import validate_ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["full-local", "audit-lite"], default="full-local")
    args = parser.parse_args()
    errors = validate_ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48(audit_lite=args.mode == "audit-lite")
    result = {"version": "V9.48", "mode": args.mode, "passed": not errors, "errors": errors}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
