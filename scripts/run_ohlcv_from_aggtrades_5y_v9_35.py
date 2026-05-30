from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.ohlcv_from_aggtrades_5y_v9_35 import run_ohlcv_from_aggtrades_5y_v9_35  # noqa: E402


def main() -> int:
    report = run_ohlcv_from_aggtrades_5y_v9_35(Path("."))
    print(
        json.dumps(
            {
                "version": report["version"],
                "decision": report["decision"],
                "quality_status": report["quality_status"],
                "coverage_status": report["coverage_status"],
                "timeframes_produced": report["timeframes_produced"],
                "row_counts": report["row_counts"],
                "runtime_seconds": report["runtime_seconds"],
                "status": report["status"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if report["decision"] in {"ohlcv_from_aggtrades_5y_derivation_complete", "ohlcv_from_aggtrades_5y_derivation_complete_with_warnings", "ohlcv_from_aggtrades_5y_derivation_partial"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
