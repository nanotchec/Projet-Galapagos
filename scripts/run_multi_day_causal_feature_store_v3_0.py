from __future__ import annotations

from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.features.multi_day import TIMEFRAMES_V3_0, run_multi_day_causal_feature_store_v3_0


def main() -> None:
    print("=== Generating Galapagos V3.0 Multi-Day Causal Feature Store Preview ===")
    manifest = run_multi_day_causal_feature_store_v3_0(Path("."))
    print(f"Status: {manifest['status']}")
    print(f"Run ID: {manifest['feature_run_id']}")
    for timeframe in TIMEFRAMES_V3_0:
        output = manifest["outputs"][timeframe]
        print(f"  {timeframe}: {output['path']} ({output['rows']} rows)")
    print("=======================================================================")


if __name__ == "__main__":
    main()
