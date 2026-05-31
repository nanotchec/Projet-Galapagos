from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.label_redesign_diagnostic_v9_63_validation import validate_label_redesign_diagnostic_v9_63


def main() -> int:
    errors = validate_label_redesign_diagnostic_v9_63(Path("."))
    print(json.dumps({"version": "V9.63", "status": "PASS" if not errors else "FAIL", "passed": not errors, "errors": errors}, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
