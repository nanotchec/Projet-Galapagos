from __future__ import annotations

import argparse
import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.features.aggtrades_exact_5y_feature_enrichment_validation_v9_46_validation import validate_aggtrades_exact_5y_feature_enrichment_validation_v9_46


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["full-local", "audit-lite"], default="full-local")
    args = parser.parse_args()
    errors = validate_aggtrades_exact_5y_feature_enrichment_validation_v9_46(mode=args.mode)
    result = {"version": "V9.46", "mode": args.mode, "passed": not errors, "errors": errors}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
