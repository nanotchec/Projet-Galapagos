from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.ml.ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62 import run_offline_ml_v9_62


def main() -> int:
    report = run_offline_ml_v9_62(Path("."))
    print(json.dumps({"version": report["version"], "decision": report["decision"], "status": report["status"]}, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
