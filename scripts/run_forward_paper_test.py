from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, datetime, timedelta

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.reports.daily_report import generate_daily_summary
from galapagos.scheduler.local_scheduler import LocalScheduler, SchedulerConfig
from galapagos.utils.paths import project_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profiles", default="30m,4h")
    parser.add_argument("--iterations", type=int, default=None)
    parser.add_argument("--sleep-seconds", type=int, default=10)
    parser.add_argument("--duration-minutes", type=int, default=None)
    parser.add_argument("--real-data", action="store_true")
    parser.add_argument("--openai-codex", action="store_true")
    parser.add_argument("--database", default=str(project_path("data/paper/galapagos.sqlite")))
    args = parser.parse_args()

    profiles = [profile.strip() for profile in args.profiles.split(",") if profile.strip()]
    deadline = (
        datetime.now(UTC) + timedelta(minutes=args.duration_minutes)
        if args.duration_minutes
        else None
    )
    iteration = 0
    all_results = []
    while True:
        scheduler = LocalScheduler(
            SchedulerConfig(
                profiles=profiles,
                database_path=args.database,
                use_real_data=args.real_data,
                use_mock_llm=not args.openai_codex,
                once=True,
            )
        )
        all_results.extend(scheduler.run())
        iteration += 1
        if args.iterations is not None and iteration >= args.iterations:
            break
        if deadline is not None and datetime.now(UTC) >= deadline:
            break
        if args.iterations is None and deadline is None:
            break
        time.sleep(args.sleep_seconds)

    succeeded = sum(1 for result in all_results if result.get("status") == "COMPLETED")
    failed = sum(1 for result in all_results if result.get("status") == "ERROR")
    report_paths = generate_daily_summary(scheduler.store, project_path("reports/daily"))
    print(
        json.dumps(
            {
                "profiles": profiles,
                "data_mode": "real" if args.real_data else "mock",
                "total_cycles": len(all_results),
                "succeeded_cycles": succeeded,
                "failed_cycles": failed,
                "results": all_results,
                "report_paths": {key: str(value) for key, value in report_paths.items()},
                "paper_trading_only": True,
            },
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    )


if __name__ == "__main__":
    main()

