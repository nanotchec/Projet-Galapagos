from __future__ import annotations

import json
import sys
from pathlib import Path

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.validation.market_data import validate_public_market_ingestion_v2_3


def main() -> None:
    result = validate_public_market_ingestion_v2_3(Path("."))
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
