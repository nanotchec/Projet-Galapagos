from __future__ import annotations

import json
from pathlib import Path

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.datasets.expanded_window_validation import validate_expanded_offline_supervised_dataset_v3_8


def main() -> None:
    result = validate_expanded_offline_supervised_dataset_v3_8(Path("."))
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
