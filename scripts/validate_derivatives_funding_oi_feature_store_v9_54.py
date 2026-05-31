from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.features.derivatives_funding_oi_feature_store_v9_54_validation import validate_derivatives_funding_oi_feature_store_file_v9_54


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["full", "audit-lite"], default="full")
    args = parser.parse_args()
    result = validate_derivatives_funding_oi_feature_store_file_v9_54(Path("."), mode=args.mode)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
