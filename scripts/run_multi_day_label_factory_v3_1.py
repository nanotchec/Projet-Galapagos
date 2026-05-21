from __future__ import annotations

import argparse
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.labels.multi_day import TIMEFRAMES_V3_1, run_multi_day_label_factory_v3_1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--validate-previous-layers",
        action="store_true",
        help="Run historical V2.3 to V3.0 validators before generating V3.1 labels.",
    )
    args = parser.parse_args()
    validate_previous_layers = bool(args.validate_previous_layers)

    print("=== Generating Galapagos V3.1 Multi-Day Clean Forward Label Factory Preview ===")
    print(f"V3.1 run mode: validate_previous_layers={validate_previous_layers}")
    if not validate_previous_layers:
        print("Historical validations are executed separately by the audit commands.")
    manifest = run_multi_day_label_factory_v3_1(
        Path("."),
        validate_previous_layers=validate_previous_layers,
    )
    print(f"Status: {manifest['status']}")
    print(f"Run ID: {manifest['label_run_id']}")
    for timeframe in TIMEFRAMES_V3_1:
        output = manifest["outputs"][timeframe]
        print(f"  {timeframe}: {output['path']} ({output['rows']} rows)")
    print("========================================================================")


if __name__ == "__main__":
    main()
