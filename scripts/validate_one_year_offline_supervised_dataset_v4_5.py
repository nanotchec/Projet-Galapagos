from __future__ import annotations

import json
from pathlib import Path

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.datasets.one_year_window_validation import validate_one_year_offline_supervised_dataset_v4_5


def main() -> None:
    result = validate_one_year_offline_supervised_dataset_v4_5(Path("."))
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
