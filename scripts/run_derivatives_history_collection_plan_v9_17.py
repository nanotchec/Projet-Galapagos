from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.derivatives_history_collection_plan_v9_17 import run_derivatives_history_collection_plan_v9_17


def main() -> int:
    report = run_derivatives_history_collection_plan_v9_17(Path("."))
    print(
        json.dumps(
            {
                "version": report["version"],
                "status": report["status"],
                "decision": report["v9_17_decision"]["decision"],
                "source_collection_candidates": len(report["source_collection_candidates"]),
                "candidate_target_windows": len(report["candidate_target_windows"]),
                "collection_executed": report["collection_executed"],
                "features_created": report["features_created"],
                "dataset_created": report["dataset_created"],
                "walk_forward_executed": report["walk_forward_executed"],
                "backtest_executed": report["backtest_executed"],
                "network_used": report["safety_flags"]["network_used"],
                "no_new_data_download": report["safety_flags"]["no_new_data_download"],
                "no_ingestion_executed": report["safety_flags"]["no_ingestion_executed"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
