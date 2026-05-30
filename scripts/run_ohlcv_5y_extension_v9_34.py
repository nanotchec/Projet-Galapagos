from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.ohlcv_5y_extension_v9_34 import run_ohlcv_5y_extension_v9_34  # noqa: E402


def main() -> int:
    report = run_ohlcv_5y_extension_v9_34(Path("."))
    print(json.dumps({
        "version": report["version"],
        "decision": report["decision"],
        "ohlcv_5y_ready": report["ohlcv_5y_ready"],
        "collection_executed": report["collection_executed"],
        "days_downloaded_total": report["days_downloaded_total"],
        "days_normalized_total": report["days_normalized_total"],
        "quality_status": report["ohlcv_quality"]["quality_status"],
        "status": report["status"],
    }, indent=2, ensure_ascii=False))
    return 0 if report["decision"] in {"ohlcv_5y_extension_complete", "ohlcv_5y_extension_partial", "ohlcv_from_aggtrades_derivation_plan_required"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
