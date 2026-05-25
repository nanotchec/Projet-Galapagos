from __future__ import annotations

import json
from pathlib import Path

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.data.public_trades.one_year_window_validation import validate_public_trades_1y_window_v8_2


def main() -> None:
    result = validate_public_trades_1y_window_v8_2(Path("."))
    printable = {key: value for key, value in result.items() if key != "manifest"}
    print(json.dumps(printable, indent=2, ensure_ascii=False))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
