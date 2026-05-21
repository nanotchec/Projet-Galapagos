from __future__ import annotations

import argparse
import json
import os
import subprocess
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
    commands: list[list[str]] = []

    with tempfile.TemporaryDirectory(prefix="galapagos_v2_8_3_smoke_") as tmp:
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

        validators = [
            ("validate_public_market_ingestion_v2_3", "galapagos.validation.market_data", "validate_public_market_ingestion_v2_3"),
            ("validate_ohlcv_resampling_v2_4", "galapagos.validation.resampling", "validate_ohlcv_resampling_v2_4"),
            ("validate_causal_feature_store_v2_5", "galapagos.features.validation", "validate_causal_feature_store_v2_5"),
            ("validate_clean_label_factory_v2_6", "galapagos.labels.validation", "validate_label_factory_v2_6"),
            ("validate_offline_supervised_dataset_v2_7", "galapagos.datasets.validation", "validate_offline_supervised_dataset_v2_7"),
            ("validate_offline_ml_research_v2_8", "galapagos.ml.validation", "validate_offline_ml_research_v2_8"),
        ]
        for label, module, function in validators:
            commands.append(
                [
                    sys.executable,
                    "-c",
                    (
                        "from pathlib import Path\n"
                        f"from {module} import {function}\n"
                        f"result = {function}(Path('.'))\n"
                        "assert result['passed'], result['errors']\n"
                        f"print('{label}: PASS')\n"
                    ),
                ]
            )

        script_check = (
            "import json\n"
            "import pandas as pd\n"
            "from galapagos.ml.schemas import ML_SCORE_COLUMNS_V2_8\n"
            f"scores={SCORES!r}\n"
            "manifest=json.load(open('reports/manifests/offline_ml_research_v2_8_manifest.json'))\n"
            "report=json.load(open('reports/ml/offline_ml_research_v2_8.json'))\n"
            "assert manifest==report\n"
            "assert manifest['version']=='V2.8'\n"
            "assert manifest['correction_version']=='V2.8.3'\n"
            "assert manifest['safety']['ml_enabled'] is True\n"
            "assert manifest['safety']['dataset_enabled'] is True\n"
            "assert manifest['safety']['labels_enabled'] is True\n"
            "assert manifest['safety']['trading_enabled'] is False\n"
            "assert manifest['safety']['backtest_enabled'] is False\n"
            "assert manifest['safety']['orders_enabled'] is False\n"
            "assert manifest['safety']['strategy_enabled'] is False\n"
            "assert manifest['safety']['execution_enabled'] is False\n"
            "for tf,path in scores.items():\n"
            "    df=pd.read_parquet(path)\n"
            "    assert list(df.columns)==ML_SCORE_COLUMNS_V2_8\n"
            "    assert len(df)==manifest['outputs'][tf]['rows']\n"
            "    assert not any(token in ' '.join(df.columns).lower() for token in ['trading_signal','order','pnl','strategy'])\n"
            "print('v2.8.3-smoke-logical-ok')\n"
        )
        commands.append([sys.executable, "-c", script_check])

        env = os.environ.copy()
        env["PYTHONPATH"] = str(tmp_path / "src")
        for command in commands:
            try:
                completed = subprocess.run(
                    command,
                    cwd=tmp_path,
                    text=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    timeout=90,
                    env=env,
                )
            except subprocess.TimeoutExpired:
                errors.append(f"command timed out: {' '.join(command)}")
                continue
            if completed.returncode != 0:
                errors.append(f"command failed: {' '.join(command)}\nstderr={completed.stderr}")

    payload = {
        "version": "V2.8",
        "correction_version": "V2.8.3",
        "zip_path": str(zip_path),
        "smoke_test_passed": not errors,
        "smoke_commands_count": len(commands),
        "smoke_failed_count": len(errors),
        "errors": errors,
    }
    Path("reports").mkdir(exist_ok=True)
    Path("reports/zip_smoke_test_v2_8_3.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path("reports/zip_smoke_test_v2_8_3.md").write_text(
        "# Smoke ZIP V2.8.3\n\n"
        f"- Statut : `{payload['smoke_test_passed']}`\n"
        f"- Commandes : `{payload['smoke_commands_count']}`\n"
        f"- Erreurs : `{payload['smoke_failed_count']}`\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
