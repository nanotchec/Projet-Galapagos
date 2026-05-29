from __future__ import annotations

import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.aggtrades_post_v9_full_coverage_validation_v9_29_validation import (  # noqa: E402
    validate_aggtrades_post_v9_full_coverage_validation_v9_29,
)


def main() -> int:
    errors = validate_aggtrades_post_v9_full_coverage_validation_v9_29()
    result = {"version": "V9.29", "status": "PASS" if not errors else "FAIL", "errors": errors}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
