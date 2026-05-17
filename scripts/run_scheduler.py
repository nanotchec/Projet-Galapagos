from __future__ import annotations

import argparse
import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.scheduler.local_scheduler import LocalScheduler, SchedulerConfig
from galapagos.utils.paths import project_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--iterations", type=int, default=None)
    parser.add_argument("--sleep-seconds", type=int, default=60)
    parser.add_argument("--profiles", default="30m,4h")
    parser.add_argument("--real-data", action="store_true")
    parser.add_argument("--openai-codex", action="store_true")
    parser.add_argument(
        "--mock-decision",
        default="NO_TRADE",
        choices=["NO_TRADE", "LONG", "SHORT", "CLOSE", "HOLD"],
    )
    parser.add_argument("--database", default=str(project_path("data/paper/galapagos.sqlite")))
    args = parser.parse_args()

    scheduler = LocalScheduler(
        SchedulerConfig(
            profiles=[profile.strip() for profile in args.profiles.split(",") if profile.strip()],
            database_path=args.database,
            use_real_data=args.real_data,
            use_mock_llm=not args.openai_codex,
            mock_decision=args.mock_decision,
            sleep_seconds=args.sleep_seconds,
            iterations=args.iterations,
            once=args.once,
        )
    )
    print(json.dumps(scheduler.run(), indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
