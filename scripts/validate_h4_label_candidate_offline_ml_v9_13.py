from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.ml.h4_label_candidate_offline_ml_v9_13_validation import validate_h4_label_candidate_offline_ml_v9_13


def main() -> int:
    errors = validate_h4_label_candidate_offline_ml_v9_13(Path("."))
    result = {"version": "V9.13", "component": "ml", "passed": not errors, "errors": errors}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
