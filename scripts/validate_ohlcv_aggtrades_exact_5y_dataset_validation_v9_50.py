from __future__ import annotations

import argparse
import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.datasets.ohlcv_aggtrades_exact_5y_dataset_validation_v9_50_validation import validate_v9_50_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["audit-lite", "full-local"], default="audit-lite")
    args = parser.parse_args()
    result = validate_v9_50_report(mode=args.mode)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
