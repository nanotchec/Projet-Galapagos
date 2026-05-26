from __future__ import annotations

import json
from pathlib import Path

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.ml.strict_walk_forward_validation import validate_strict_walk_forward_validation_v8_7


def main() -> None:
    result = validate_strict_walk_forward_validation_v8_7(Path("."))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
