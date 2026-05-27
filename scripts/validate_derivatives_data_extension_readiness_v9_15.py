from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.derivatives_data_extension_readiness_v9_15_validation import validate_derivatives_data_extension_readiness_v9_15


def main() -> int:
    errors = validate_derivatives_data_extension_readiness_v9_15(Path("."))
    result = {"version": "V9.15", "passed": not errors, "errors": errors}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
