from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.experiments.experiment_runner import run_experiment
from galapagos.utils.config_loader import load_yaml
from galapagos.utils.paths import project_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--iterations", type=int, default=None)
    parser.add_argument("--sleep-seconds", type=int, default=60)
    parser.add_argument("--generate-report", action="store_true")
    parser.add_argument("--database", default=str(project_path("data/paper/galapagos.sqlite")))
    args = parser.parse_args()

    experiment = load_yaml(args.config)
    result = run_experiment(
        experiment,
        database_path=args.database,
        once=args.once,
        iterations=args.iterations,
        sleep_seconds=args.sleep_seconds,
        generate_report=args.generate_report,
    )
    print(json.dumps(asdict(result), indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
