from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path


EXPECTED_ROWS = {"1m": 10080, "5m": 2016, "15m": 672, "1h": 168}
OUTPUTS = {
    timeframe: f"data/research/v2_9/silver/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe={timeframe}/window=2024-01-15_2024-01-21/ohlcv.parquet"
    for timeframe in EXPECTED_ROWS
}
FORBIDDEN_PREFIXES = [
    "reports/backtests/",
    "reports/strategies/",
    "reports/signals/",
    "reports/predictions/",
    "models/",
    "checkpoints/",
    "orders/",
    "execution/",
]
FORBIDDEN_SUFFIXES = {".pkl", ".pickle", ".joblib", ".ckpt", ".pt", ".pth", ".onnx"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True)
    args = parser.parse_args()
    zip_path = Path(args.zip).resolve()
    errors: list[str] = []
    validators_run = 0
    with tempfile.TemporaryDirectory(prefix="galapagos_v2_9_smoke_") as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            names = archive.namelist()
            archive.extractall(tmp_path)
        for prefix in FORBIDDEN_PREFIXES:
            if any(name.startswith(prefix) for name in names):
                errors.append(f"forbidden zip prefix: {prefix}")
        for name in names:
            if Path(name).suffix.casefold() in FORBIDDEN_SUFFIXES:
                errors.append(f"forbidden model artifact: {name}")
        sys.path.insert(0, str(tmp_path / "src"))
        previous_cwd = Path.cwd()
        os.chdir(tmp_path)
        try:
            import pandas as pd

            from galapagos.data.public_market.multi_day_validation import validate_multi_day_public_market_data_v2_9
            from galapagos.data.public_market.schemas import OHLCV_COLUMNS
            from galapagos.datasets.validation import validate_offline_supervised_dataset_v2_7
            from galapagos.features.validation import validate_causal_feature_store_v2_5
            from galapagos.labels.validation import validate_label_factory_v2_6
            from galapagos.ml.validation import validate_offline_ml_research_v2_8
            from galapagos.validation.market_data import validate_public_market_ingestion_v2_3
            from galapagos.validation.resampling import validate_ohlcv_resampling_v2_4

            validators = [
                validate_public_market_ingestion_v2_3,
                validate_ohlcv_resampling_v2_4,
                validate_causal_feature_store_v2_5,
                validate_label_factory_v2_6,
                validate_offline_supervised_dataset_v2_7,
                validate_offline_ml_research_v2_8,
                validate_multi_day_public_market_data_v2_9,
            ]
            for validator in validators:
                result = validator(tmp_path)
                validators_run += 1
                if not result["passed"]:
                    errors.append(f"{validator.__name__} failed: {result['errors']}")
            manifest = json.loads(Path("reports/manifests/multi_day_public_market_data_v2_9_manifest.json").read_text(encoding="utf-8"))
            for timeframe, path in OUTPUTS.items():
                frame = pd.read_parquet(path)
                if list(frame.columns) != OHLCV_COLUMNS:
                    errors.append(f"OHLCV schema mismatch: {timeframe}")
                if len(frame) != EXPECTED_ROWS[timeframe]:
                    errors.append(f"row count mismatch: {timeframe}")
                if manifest["outputs"][timeframe]["rows"] != EXPECTED_ROWS[timeframe]:
                    errors.append(f"manifest row count mismatch: {timeframe}")
            safety = manifest.get("safety", {})
            for flag in ["trading_enabled", "backtest_enabled", "orders_enabled", "strategy_enabled", "execution_enabled"]:
                if safety.get(flag) is not False:
                    errors.append(f"unsafe V2.9 flag active: {flag}")
        except Exception as exc:
            errors.append(f"smoke validation failed: {exc}")
        finally:
            os.chdir(previous_cwd)
    payload = {
        "version": "V2.9.1",
        "zip_path": str(zip_path),
        "smoke_test_passed": not errors,
        "smoke_validators_run": validators_run,
        "smoke_failed_count": len(errors),
        "errors": errors,
    }
    Path("reports").mkdir(exist_ok=True)
    Path("reports/zip_smoke_test_v2_9_1.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path("reports/zip_smoke_test_v2_9_1.md").write_text(
        "# Smoke ZIP V2.9.1\n\n"
        f"- Statut : `{payload['smoke_test_passed']}`\n"
        f"- Validateurs : `{payload['smoke_validators_run']}`\n"
        f"- Erreurs : `{payload['smoke_failed_count']}`\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
