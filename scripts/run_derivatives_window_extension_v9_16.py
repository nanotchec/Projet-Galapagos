from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.derivatives_window_extension_v9_16 import run_derivatives_window_extension_v9_16


def main() -> int:
    report = run_derivatives_window_extension_v9_16(Path("."))
    print(
        json.dumps(
            {
                "version": report["version"],
                "status": report["status"],
                "decision": report["v9_16_decision"]["decision"],
                "candidate_windows": len(report["candidate_windows"]),
                "data_sources": len(report["data_sources_inventory"]),
                "features_created": report["features_created"],
                "dataset_created": report["dataset_created"],
                "walk_forward_executed": report["walk_forward_executed"],
                "backtest_executed": report["backtest_executed"],
                "network_used": report["safety_flags"]["network_used"],
                "no_new_data_download": report["safety_flags"]["no_new_data_download"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
