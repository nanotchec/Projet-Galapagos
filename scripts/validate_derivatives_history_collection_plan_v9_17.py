from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.derivatives_history_collection_plan_v9_17_validation import validate_derivatives_history_collection_plan_v9_17


def main() -> int:
    errors = validate_derivatives_history_collection_plan_v9_17(Path("."))
    result = {"version": "V9.17", "passed": not errors, "errors": errors}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
