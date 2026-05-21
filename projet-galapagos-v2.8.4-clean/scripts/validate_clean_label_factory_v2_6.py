from __future__ import annotations

import json
from pathlib import Path

import _bootstrap
_bootstrap.bootstrap_src_path()

from galapagos.labels.validation import validate_label_factory_v2_6


def main() -> None:
    result = validate_label_factory_v2_6(Path("."))
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
