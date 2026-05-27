from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.alternative_label_design_audit_v9_5_validation import validate_alternative_label_design_audit_v9_5


def main() -> int:
    errors = validate_alternative_label_design_audit_v9_5(Path("."))
    result = {"version": "V9.5", "passed": not errors, "errors": errors}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
