from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.datasets.max_history_window_validation import validate_max_history_offline_supervised_dataset_v5_3


def main() -> None:
    result = validate_max_history_offline_supervised_dataset_v5_3(Path("."))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
