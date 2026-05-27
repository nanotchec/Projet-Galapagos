from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.labels.horizon_event_label_redesign_v9_12_validation import validate_horizon_event_label_redesign_v9_12


def main() -> int:
    errors = validate_horizon_event_label_redesign_v9_12(Path("."))
    result = {"version": "V9.12", "passed": not errors, "errors": errors}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
