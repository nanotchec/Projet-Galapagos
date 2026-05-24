from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.labels.max_history_window_validation import validate_max_history_label_factory_v5_2


def main() -> None:
    result = validate_max_history_label_factory_v5_2(Path("."))
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
