from __future__ import annotations

import json
import argparse

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.datasets.ohlcv_aggtrades_exact_5y_dataset_v9_49_validation import validate_v9_49_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["full-local", "audit-lite"], default="full-local")
    args = parser.parse_args()
    result = validate_v9_49_report(audit_lite=args.mode == "audit-lite")
    result["mode"] = args.mode
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
