from __future__ import annotations

from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.features.advanced_ohlcv import TIMEFRAMES_V6_0, run_advanced_ohlcv_feature_store_v6_0


def main() -> None:
    print("=== Generating Galapagos V6.0 Advanced OHLCV Feature Store ===")
    print("V6.0 run mode: validate_inputs=True")
    print("Only validate_max_history_public_market_data_v5_0 is called before feature generation.")
    manifest = run_advanced_ohlcv_feature_store_v6_0(Path("."))
    print(f"Status: {manifest['status']}")
    print(f"Run ID: {manifest['feature_run_id']}")
    print(
        "Input window: "
        f"{manifest['input_ohlcv_manifest']['window_start']} -> "
        f"{manifest['input_ohlcv_manifest']['window_end']}"
    )
    print(f"Feature columns: {len(manifest['feature_columns'])}")
    for timeframe in TIMEFRAMES_V6_0:
        output = manifest["outputs"][timeframe]
        quality = manifest["quality"][timeframe]
        print(
            f"  {timeframe}: {output['path']} ({output['rows']} rows, "
            f"warmup={quality['warmup_rows']}, sha256={output['sha256']})"
        )
    print("================================================================")


if __name__ == "__main__":
    main()
