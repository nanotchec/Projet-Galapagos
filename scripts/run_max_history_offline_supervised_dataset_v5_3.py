from __future__ import annotations

from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.datasets.max_history_window import TIMEFRAMES_V5_3, run_max_history_offline_supervised_dataset_v5_3


def main() -> None:
    print("=== Generating Galapagos V5.3 Max Historical Offline Supervised Dataset Preview ===")
    print("V5.3 run mode: validate_inputs=True")
    print("Only V5.1 feature and V5.2 label validators are called before dataset assembly.")
    manifest = run_max_history_offline_supervised_dataset_v5_3(Path("."))
    print(f"Status: {manifest['status']}")
    print(f"Run ID: {manifest['dataset_run_id']}")
    print(
        "Input window: "
        f"{manifest['input_features_manifest']['window_start']} -> "
        f"{manifest['input_features_manifest']['window_end']}"
    )
    for timeframe in TIMEFRAMES_V5_3:
        output = manifest["outputs"][timeframe]
        split = manifest["splits"][timeframe]
        print(f"  {timeframe}: dataset {output['path']} ({output['rows']} rows)")
        print(f"  {timeframe}: splits  {split['path']} ({split['rows']} rows)")
    print("===============================================================================")


if __name__ == "__main__":
    main()
