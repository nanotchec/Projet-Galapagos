from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.labels.redesigned_5y_label_factory_v9_64_validation import validate_redesigned_5y_label_factory_v9_64


def main() -> int:
    errors = validate_redesigned_5y_label_factory_v9_64(Path("."))
    print(json.dumps({"version": "V9.64", "status": "PASS" if not errors else "FAIL", "passed": not errors, "errors": errors}, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
