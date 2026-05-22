from __future__ import annotations

import json
from pathlib import Path

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.ml.expanded_window_validation import validate_expanded_offline_ml_research_v3_9


def main() -> None:
    result = validate_expanded_offline_ml_research_v3_9(Path("."))
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
