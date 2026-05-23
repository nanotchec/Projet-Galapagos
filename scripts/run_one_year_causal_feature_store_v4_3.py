from __future__ import annotations

from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.features.one_year_window import TIMEFRAMES_V4_3, run_one_year_causal_feature_store_v4_3


def main() -> None:
    print("=== Generating Galapagos V4.3 1-Year Causal Feature Store Preview ===")
    print("V4.3 run mode: validate_inputs=True")
    print("Only validate_one_year_public_market_data_v4_2 is called before feature generation.")
    manifest = run_one_year_causal_feature_store_v4_3(Path("."))
    print(f"Status: {manifest['status']}")
    print(f"Run ID: {manifest['feature_run_id']}")
    for timeframe in TIMEFRAMES_V4_3:
        output = manifest["outputs"][timeframe]
        print(f"  {timeframe}: {output['path']} ({output['rows']} rows)")
    print("====================================================================")


if __name__ == "__main__":
    main()
