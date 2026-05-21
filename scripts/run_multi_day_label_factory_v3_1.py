from __future__ import annotations

from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.labels.multi_day import TIMEFRAMES_V3_1, run_multi_day_label_factory_v3_1


def main() -> None:
    print("=== Generating Galapagos V3.1 Multi-Day Clean Forward Label Factory Preview ===")
    manifest = run_multi_day_label_factory_v3_1(Path("."))
    print(f"Status: {manifest['status']}")
    print(f"Run ID: {manifest['label_run_id']}")
    for timeframe in TIMEFRAMES_V3_1:
        output = manifest["outputs"][timeframe]
        print(f"  {timeframe}: {output['path']} ({output['rows']} rows)")
    print("========================================================================")


if __name__ == "__main__":
    main()
