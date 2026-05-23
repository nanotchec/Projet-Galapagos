from __future__ import annotations

import json
from pathlib import Path

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.ml.one_year_window_validation import validate_one_year_offline_ml_research_v4_6


def main() -> None:
    result = validate_one_year_offline_ml_research_v4_6(Path("."))
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
