from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.ohlcv_from_aggtrades_5y_validation_v9_36 import run_ohlcv_from_aggtrades_5y_validation_v9_36  # noqa: E402


def main() -> int:
    report = run_ohlcv_from_aggtrades_5y_validation_v9_36(Path("."))
    print(
        json.dumps(
            {
                "version": report["version"],
                "decision": report["decision"],
                "coverage_status": report["coverage_status"],
                "quality_status": report["quality_status"],
                "parity_status": report["parity_status"],
                "runtime_seconds": report["runtime_seconds"],
                "status": report["status"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if report["decision"] in {"ohlcv_from_aggtrades_5y_validation_pass", "ohlcv_from_aggtrades_5y_validation_pass_with_non_blocking_warnings"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
