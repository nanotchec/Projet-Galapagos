from __future__ import annotations

import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.aggtrades_5y_full_coverage_validation_v9_32_validation import (
    validate_aggtrades_5y_full_coverage_validation_v9_32,
)


def main() -> int:
    errors = validate_aggtrades_5y_full_coverage_validation_v9_32()
    print(json.dumps({"version": "V9.32", "status": "PASS" if not errors else "FAIL", "errors": errors}, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
