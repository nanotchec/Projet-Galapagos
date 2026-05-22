from __future__ import annotations

from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.labels.expanded_window import TIMEFRAMES_V3_7, run_expanded_label_factory_v3_7


def main() -> None:
    print("=== Generating Galapagos V3.7 90-Day Clean Forward Label Factory Preview ===")
    print("V3.7 run mode: validate_inputs=True")
    print("Only validate_expanded_public_market_data_v3_5 is called before label generation.")
    manifest = run_expanded_label_factory_v3_7(Path("."))
    print(f"Status: {manifest['status']}")
    print(f"Run ID: {manifest['label_run_id']}")
    for timeframe in TIMEFRAMES_V3_7:
        output = manifest["outputs"][timeframe]
        print(f"  {timeframe}: {output['path']} ({output['rows']} rows)")
    print("==========================================================================")


if __name__ == "__main__":
    main()
