from __future__ import annotations

import argparse
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.datasets.multi_day import run_multi_day_offline_supervised_dataset_v3_2
from galapagos.datasets.schemas import TIMEFRAMES_V3_2


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--validate-full-history",
        action="store_true",
        help="Run historical V2.3 to V2.8 validators before assembling V3.2. Disabled by default.",
    )
    parser.add_argument(
        "--skip-recent-validation",
        action="store_true",
        help="Skip V2.9/V3.0/V3.1 validators. Intended only for targeted tests.",
    )
    args = parser.parse_args()
    validate_recent_layers = not args.skip_recent_validation

    print("=== Generating Galapagos V3.2 Multi-Day Offline Supervised Dataset Preview ===")
    print(f"V3.2 run mode: validate_recent_layers={validate_recent_layers}")
    print(f"V3.2 run mode: validate_full_history={bool(args.validate_full_history)}")
    if not args.validate_full_history:
        print("Historical V2.3 to V2.8 validations are executed separately by audit commands.")
    manifest = run_multi_day_offline_supervised_dataset_v3_2(
        Path("."),
        validate_recent_layers=validate_recent_layers,
        validate_full_history=bool(args.validate_full_history),
    )
    print(f"Status: {manifest['status']}")
    print(f"Run ID: {manifest['dataset_run_id']}")
    for timeframe in TIMEFRAMES_V3_2:
        output = manifest["outputs"][timeframe]
        split = manifest["splits"][timeframe]
        print(f"  {timeframe}: {output['path']} ({output['rows']} rows), splits={split['rows']}")
    print("========================================================================")


if __name__ == "__main__":
    main()
