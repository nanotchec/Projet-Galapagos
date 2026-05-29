from __future__ import annotations

import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.aggtrades_5y_extension_collection_v9_31_validation import validate_aggtrades_5y_extension_collection_v9_31  # noqa: E402


def main() -> int:
    errors = validate_aggtrades_5y_extension_collection_v9_31()
    result = {"version": "V9.31", "status": "PASS" if not errors else "FAIL", "errors": errors}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
