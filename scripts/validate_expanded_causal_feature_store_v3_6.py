from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.features.expanded_window_validation import validate_expanded_causal_feature_store_v3_6


def main() -> None:
    result = validate_expanded_causal_feature_store_v3_6(Path("."))
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
