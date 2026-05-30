from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.features.ohlcv_aggtrades_5y_feature_store_v9_33 import (  # noqa: E402
    run_ohlcv_aggtrades_5y_feature_store_v9_33,
)


def main() -> int:
    report = run_ohlcv_aggtrades_5y_feature_store_v9_33(Path("."))
    print(json.dumps({
        "version": report["version"],
        "decision": report["decision"],
        "ohlcv_5y_ready": report["ohlcv_readiness"]["ohlcv_5y_ready"],
        "aggtrades_5y_ready": report["aggtrades_readiness"]["aggtrades_5y_ready"],
        "feature_store_created": report["feature_store_created"],
        "quality_status": report["quality_status"],
        "status": report["status"],
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
