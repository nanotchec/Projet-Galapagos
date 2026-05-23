from __future__ import annotations

from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.labels.one_year_window import TIMEFRAMES_V4_4, run_one_year_label_factory_v4_4


def main() -> None:
    print("=== Generating Galapagos V4.4 1-Year Clean Forward Label Factory Preview ===")
    print("V4.4 run mode: validate_inputs=True")
    print("Only validate_one_year_public_market_data_v4_2 is called before label generation.")
    manifest = run_one_year_label_factory_v4_4(Path("."))
    print(f"Status: {manifest['status']}")
    print(f"Run ID: {manifest['label_run_id']}")
    for timeframe in TIMEFRAMES_V4_4:
        output = manifest["outputs"][timeframe]
        print(f"  {timeframe}: {output['path']} ({output['rows']} rows)")
    print("==========================================================================")


if __name__ == "__main__":
    main()
