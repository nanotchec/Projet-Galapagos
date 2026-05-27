from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.label_failure_analysis_v9_11_validation import validate_label_failure_analysis_v9_11


def main() -> int:
    errors = validate_label_failure_analysis_v9_11(Path("."))
    result = {"version": "V9.11", "passed": not errors, "errors": errors}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
