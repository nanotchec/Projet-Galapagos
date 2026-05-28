from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.aggtrades_post_v9_storage_resume_campaign_v9_26 import (  # noqa: E402
    run_aggtrades_post_v9_storage_resume_campaign_v9_26,
)


def main() -> int:
    report = run_aggtrades_post_v9_storage_resume_campaign_v9_26(Path("."))
    print(
        json.dumps(
            {
                "version": report["version"],
                "decision": report["decision"],
                "free_gib_data_mount": report["disk_preflight"]["free_gib_data_mount"],
                "first_missing_day_before_resume": report["first_missing_day_before_resume"],
                "local_file_coverage_start": report["local_file_coverage_start"],
                "local_file_coverage_end": report["local_file_coverage_end"],
                "days_downloaded_total": report["days_downloaded_total"],
                "days_complete_total": report["days_complete_total"],
                "complete_collection_reached": report["complete_collection_reached"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
