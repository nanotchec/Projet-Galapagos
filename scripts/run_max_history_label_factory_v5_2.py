from __future__ import annotations

from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.labels.max_history_window import TIMEFRAMES_V5_2, run_max_history_label_factory_v5_2


def main() -> None:
    print("=== Generating Galapagos V5.2 Max Historical Clean Forward Label Factory Preview ===")
    print("V5.2 run mode: validate_inputs=True")
    print("Only validate_max_history_public_market_data_v5_0 is called before label generation.")
    manifest = run_max_history_label_factory_v5_2(Path("."))
    print(f"Status: {manifest['status']}")
    print(f"Run ID: {manifest['label_run_id']}")
    print(
        "Input window: "
        f"{manifest['input_ohlcv_manifest']['window_start']} -> "
        f"{manifest['input_ohlcv_manifest']['window_end']}"
    )
    for timeframe in TIMEFRAMES_V5_2:
        output = manifest["outputs"][timeframe]
        print(f"  {timeframe}: {output['path']} ({output['rows']} rows)")
    print("==============================================================================")


if __name__ == "__main__":
    main()
