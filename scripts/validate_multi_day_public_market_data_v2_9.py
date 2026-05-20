from __future__ import annotations

import json
from pathlib import Path

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.data.public_market.multi_day_validation import validate_multi_day_public_market_data_v2_9


def main() -> None:
    result = validate_multi_day_public_market_data_v2_9(Path("."))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
