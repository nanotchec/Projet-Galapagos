from __future__ import annotations

from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.features.expanded_window import TIMEFRAMES_V3_6, run_expanded_causal_feature_store_v3_6


def main() -> None:
    print("=== Generating Galapagos V3.6 90-Day Causal Feature Store Preview ===")
    print("V3.6 run mode: validate_inputs=True")
    print("Only validate_expanded_public_market_data_v3_5 is called before feature generation.")
    manifest = run_expanded_causal_feature_store_v3_6(Path("."))
    print(f"Status: {manifest['status']}")
    print(f"Run ID: {manifest['feature_run_id']}")
    for timeframe in TIMEFRAMES_V3_6:
        output = manifest["outputs"][timeframe]
        print(f"  {timeframe}: {output['path']} ({output['rows']} rows)")
    print("====================================================================")


if __name__ == "__main__":
    main()
