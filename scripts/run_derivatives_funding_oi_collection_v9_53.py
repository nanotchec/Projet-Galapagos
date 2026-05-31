from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.derivatives_funding_oi_collection_v9_53 import run_derivatives_funding_oi_collection_v9_53


def main() -> int:
    report = run_derivatives_funding_oi_collection_v9_53(Path("."))
    print(json.dumps({"version": report["version"], "decision": report["decision"], "status": report["status"]}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
