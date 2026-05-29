from __future__ import annotations

import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.aggtrades_5y_extension_plan_v9_30 import run_aggtrades_5y_extension_plan_v9_30  # noqa: E402


def main() -> int:
    report = run_aggtrades_5y_extension_plan_v9_30()
    summary = {
        "version": report["version"],
        "decision": report["decision"],
        "target_5y_window_start": report["target_5y_window_start"],
        "target_5y_window_end": report["target_5y_window_end"],
        "extension_days_needed": report["extension_days_needed"],
        "estimated_extension_raw_bytes": report["estimated_extension_raw_bytes"],
        "estimated_extension_silver_bytes": report["estimated_extension_silver_bytes"],
        "free_gib_data_mount": report["free_gib_data_mount"],
        "safe_for_5y_extension_collection": report["safe_for_5y_extension_collection"],
        "network_used": report["network_used"],
        "new_data_downloaded": report["new_data_downloaded"],
        "ingestion_executed": report["ingestion_executed"],
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
