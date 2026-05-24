from __future__ import annotations

from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.datasets.advanced_ohlcv_window import TIMEFRAMES_V6_1, run_advanced_ohlcv_offline_supervised_dataset_v6_1


def main() -> None:
    print("=== Generating Galapagos V6.1 Advanced OHLCV Offline Supervised Dataset ===")
    print("V6.1 run mode: validate_inputs=True")
    print("Only V6.0 advanced features and V5.2 labels validators are called before dataset assembly.")
    manifest = run_advanced_ohlcv_offline_supervised_dataset_v6_1(Path("."))
    print(f"Status: {manifest['status']}")
    print(f"Run ID: {manifest['dataset_run_id']}")
    print(
        "Input window: "
        f"{manifest['input_features_manifest']['window_start']} -> "
        f"{manifest['input_features_manifest']['window_end']}"
    )
    print(f"Advanced feature columns count: {manifest['advanced_feature_columns_count']}")
    for timeframe in TIMEFRAMES_V6_1:
        output = manifest["outputs"][timeframe]
        split = manifest["splits"][timeframe]
        quality = manifest["quality"][timeframe]
        print(
            f"  {timeframe}: dataset={output['path']} ({output['rows']} rows, sha256={output['sha256']}); "
            f"splits={split['path']} ({split['rows']} rows); split_counts={quality['split_counts']}"
        )
    print("==============================================================================")


if __name__ == "__main__":
    main()
