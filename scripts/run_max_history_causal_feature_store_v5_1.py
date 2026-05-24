from __future__ import annotations

from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.features.max_history_window import TIMEFRAMES_V5_1, run_max_history_causal_feature_store_v5_1


def main() -> None:
    print("=== Generating Galapagos V5.1 Max Historical Causal Feature Store Preview ===")
    print("V5.1 run mode: validate_inputs=True")
    print("Only validate_max_history_public_market_data_v5_0 is called before feature generation.")
    manifest = run_max_history_causal_feature_store_v5_1(Path("."))
    print(f"Status: {manifest['status']}")
    print(f"Run ID: {manifest['feature_run_id']}")
    print(
        "Input window: "
        f"{manifest['input_ohlcv_manifest']['window_start']} -> "
        f"{manifest['input_ohlcv_manifest']['window_end']}"
    )
    for timeframe in TIMEFRAMES_V5_1:
        output = manifest["outputs"][timeframe]
        print(f"  {timeframe}: {output['path']} ({output['rows']} rows)")
    print("============================================================================")


if __name__ == "__main__":
    main()
