from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path


SCORES = {
    "1m": "data/gold/ml/offline_research/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/year=2024/month=01/ml-scores-2024-01-15.parquet",
    "5m": "data/gold/ml/offline_research/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/year=2024/month=01/ml-scores-2024-01-15.parquet",
    "15m": "data/gold/ml/offline_research/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/year=2024/month=01/ml-scores-2024-01-15.parquet",
    "1h": "data/gold/ml/offline_research/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/year=2024/month=01/ml-scores-2024-01-15.parquet",
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

    with tempfile.TemporaryDirectory(prefix="galapagos_v2_8_4_smoke_") as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            names = archive.namelist()
            archive.extractall(tmp_path)

        required = [
            "reports/manifests/offline_ml_research_v2_8_manifest.json",
            "reports/ml/offline_ml_research_v2_8.json",
            "reports/ml/offline_ml_research_v2_8.md",
            *SCORES.values(),
        ]
        for relative in required:
            if not (tmp_path / relative).exists():
                errors.append(f"missing smoke file: {relative}")

        for prefix in FORBIDDEN_PREFIXES:
            if any(name.startswith(prefix) for name in names):
                errors.append(f"forbidden zip prefix: {prefix}")
        for name in names:
            if Path(name).suffix.casefold() in FORBIDDEN_SUFFIXES:
                errors.append(f"forbidden model artifact: {name}")
            if name.startswith("data/gold/ml/") and not (name.endswith("/ml-scores-2024-01-15.parquet") and "/offline_research/" in name):
                errors.append(f"unexpected data/gold/ml entry: {name}")
        forbidden_parts = [".git/", ".venv/", "__pycache__/", ".pytest_cache/", ".ruff_cache/", ".mypy_cache/"]
        for part in forbidden_parts:
            if any(part in name for name in names):
                errors.append(f"forbidden zip entry part: {part}")

        sys.path.insert(0, str(tmp_path / "src"))
        previous_cwd = Path.cwd()
        os.chdir(tmp_path)
        try:
            import pandas as pd

            from galapagos.datasets.validation import validate_offline_supervised_dataset_v2_7
            from galapagos.features.validation import validate_causal_feature_store_v2_5
            from galapagos.labels.validation import validate_label_factory_v2_6
            from galapagos.ml.schemas import ML_SCORE_COLUMNS_V2_8
            from galapagos.ml.validation import validate_offline_ml_research_v2_8
            from galapagos.validation.market_data import validate_public_market_ingestion_v2_3
            from galapagos.validation.resampling import validate_ohlcv_resampling_v2_4

            validators = [
                ("validate_public_market_ingestion_v2_3", validate_public_market_ingestion_v2_3),
                ("validate_ohlcv_resampling_v2_4", validate_ohlcv_resampling_v2_4),
                ("validate_causal_feature_store_v2_5", validate_causal_feature_store_v2_5),
                ("validate_clean_label_factory_v2_6", validate_label_factory_v2_6),
                ("validate_offline_supervised_dataset_v2_7", validate_offline_supervised_dataset_v2_7),
                ("validate_offline_ml_research_v2_8", validate_offline_ml_research_v2_8),
            ]
            for label, validator in validators:
                result = validator(tmp_path)
                validators_run += 1
                if not result["passed"]:
                    errors.append(f"{label} failed: {result['errors']}")

            manifest = json.loads(Path("reports/manifests/offline_ml_research_v2_8_manifest.json").read_text(encoding="utf-8"))
            report = json.loads(Path("reports/ml/offline_ml_research_v2_8.json").read_text(encoding="utf-8"))
            if manifest != report:
                errors.append("V2.8 manifest/report mismatch")
            if manifest.get("version") != "V2.8":
                errors.append("V2.8 manifest version mismatch")
            if manifest.get("correction_version") != "V2.8.4":
                errors.append("V2.8 correction_version mismatch")
            safety = manifest.get("safety", {})
            for flag in ["trading_enabled", "backtest_enabled", "orders_enabled", "strategy_enabled", "execution_enabled"]:
                if safety.get(flag) is not False:
                    errors.append(f"unsafe V2.8 flag active: {flag}")
            for flag in ["ml_enabled", "dataset_enabled", "labels_enabled"]:
                if safety.get(flag) is not True:
                    errors.append(f"expected V2.8 flag inactive: {flag}")
            for timeframe, path in SCORES.items():
                frame = pd.read_parquet(path)
                if list(frame.columns) != ML_SCORE_COLUMNS_V2_8:
                    errors.append(f"V2.8 score schema mismatch: {timeframe}")
                if len(frame) != manifest["outputs"][timeframe]["rows"]:
                    errors.append(f"V2.8 score row mismatch: {timeframe}")
                joined_columns = " ".join(frame.columns).lower()
                if any(token in joined_columns for token in ["trading_signal", "order", "pnl", "strategy"]):
                    errors.append(f"forbidden V2.8 score column name: {timeframe}")
        except Exception as exc:
            errors.append(f"smoke validation failed: {exc}")
        finally:
            os.chdir(previous_cwd)

    payload = {
        "version": "V2.8",
        "correction_version": "V2.8.4",
        "zip_path": str(zip_path),
        "smoke_test_passed": not errors,
        "smoke_validators_run": validators_run,
        "smoke_failed_count": len(errors),
        "errors": errors,
    }
    Path("reports").mkdir(exist_ok=True)
    Path("reports/zip_smoke_test_v2_8_4.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path("reports/zip_smoke_test_v2_8_4.md").write_text(
        "# Smoke ZIP V2.8.4\n\n"
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
