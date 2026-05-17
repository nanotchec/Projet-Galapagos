from __future__ import annotations

import argparse
import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.reports.data_readiness_report import (
    assess_data_readiness,
    generate_data_readiness_report,
)
from galapagos.utils.config_loader import load_profile
from galapagos.utils.paths import project_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--profile",
        default="30m",
        choices=["30m", "4h", "galapagos_30m", "galapagos_4h"],
    )
    parser.add_argument("--real-data", action="store_true")
    args = parser.parse_args()
    readiness = assess_data_readiness(load_profile(args.profile), use_real_data=args.real_data)
    paths = generate_data_readiness_report(readiness, project_path("reports/diagnostics"))
    print(
        json.dumps(
            {"readiness": readiness, "paths": {k: str(v) for k, v in paths.items()}},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
