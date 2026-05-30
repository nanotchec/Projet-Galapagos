from __future__ import annotations

import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.ml.ohlcv_aggtrades_5y_offline_ml_v9_43 import run_offline_ml_v9_43


if __name__ == "__main__":
    report = run_offline_ml_v9_43()
    print(json.dumps({"version": report["version"], "decision": report["decision"], "quality_status": report["quality_status"], "runtime_seconds": report["runtime_seconds"]}, indent=2, ensure_ascii=False))

