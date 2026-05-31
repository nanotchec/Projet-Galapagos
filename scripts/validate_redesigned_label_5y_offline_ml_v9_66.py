from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.ml.redesigned_label_5y_offline_ml_v9_66_validation import validate_redesigned_label_5y_offline_ml_v9_66


def main() -> int:
    errors = validate_redesigned_label_5y_offline_ml_v9_66(Path("."))
    print(json.dumps({"version": "V9.66", "status": "PASS" if not errors else "FAIL", "passed": not errors, "errors": errors}, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
