from __future__ import annotations

import json
from pathlib import Path

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.ml.max_history_robustness_validation import validate_max_history_ml_robustness_v5_5


def main() -> None:
    result = validate_max_history_ml_robustness_v5_5(Path("."))
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
