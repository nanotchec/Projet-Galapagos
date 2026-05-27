from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.derivatives_window_extension_v9_16_validation import validate_derivatives_window_extension_v9_16


def main() -> int:
    errors = validate_derivatives_window_extension_v9_16(Path("."))
    result = {"version": "V9.16", "passed": not errors, "errors": errors}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
