from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.labels.horizon_event_label_redesign_v9_12 import run_horizon_event_label_redesign_v9_12


def main() -> int:
    report = run_horizon_event_label_redesign_v9_12(Path("."))
    print(
        json.dumps(
            {
                "version": report["version"],
                "status": report["status"],
                "decision": report["v9_12_decision"]["decision"],
                "recommended_candidate": report["recommended_candidate"]["target_name"],
                "full_data_available": report["full_data_available"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
