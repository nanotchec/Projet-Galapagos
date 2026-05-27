from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.feature_label_separability_v9_14_1_validation import validate_feature_label_separability_v9_14_1


def main() -> int:
    errors = validate_feature_label_separability_v9_14_1(Path("."))
    result = {"version": "V9.14.1", "passed": not errors, "errors": errors}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
