from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


DATASETS = {
    "1m": "data/gold/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/year=2024/month=01/dataset-2024-01-15.parquet",
    "5m": "data/gold/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/year=2024/month=01/dataset-2024-01-15.parquet",
    "15m": "data/gold/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/year=2024/month=01/dataset-2024-01-15.parquet",
    "1h": "data/gold/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/year=2024/month=01/dataset-2024-01-15.parquet",
}
EXPECTED_ROWS = {"1m": 1440, "5m": 288, "15m": 96, "1h": 24}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True)
    args = parser.parse_args()
    zip_path = Path(args.zip).resolve()
    errors: list[str] = []
    commands: list[list[str]] = []

    with tempfile.TemporaryDirectory(prefix="galapagos_v2_7_smoke_") as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            names = archive.namelist()
            archive.extractall(tmp_path)

        required = [
            "reports/manifests/offline_supervised_dataset_v2_7_manifest.json",
            "reports/datasets/offline_supervised_dataset_v2_7.json",
            "reports/datasets/offline_supervised_dataset_v2_7_datacard.md",
            *DATASETS.values(),
        ]
        for relative in required:
            if not (tmp_path / relative).exists():
                errors.append(f"missing smoke file: {relative}")

        forbidden_prefixes = ["models/", "reports/ml/", "reports/backtests/", "reports/strategies/", "reports/signals/", "reports/predictions/", "orders/", "execution/"]
        forbidden_parts = [".git/", ".venv/", "__pycache__/", ".pytest_cache/", ".ruff_cache/", ".mypy_cache/"]
        for prefix in forbidden_prefixes:
            if any(name.startswith(prefix) for name in names):
                errors.append(f"forbidden zip prefix: {prefix}")
        for part in forbidden_parts:
            if any(part in name for name in names):
                errors.append(f"forbidden zip entry part: {part}")

        commands.extend(
            [
                [sys.executable, "scripts/validate_public_market_ingestion_v2_3.py"],
                [sys.executable, "scripts/validate_ohlcv_resampling_v2_4.py"],
                [sys.executable, "scripts/validate_causal_feature_store_v2_5.py"],
                [sys.executable, "scripts/validate_clean_label_factory_v2_6.py"],
                [sys.executable, "scripts/validate_offline_supervised_dataset_v2_7.py"],
            ]
        )

        script_check = (
            "import json\n"
            "import pandas as pd\n"
            "from galapagos.datasets.schemas import DATASET_COLUMNS_V2_7\n"
            f"datasets={DATASETS!r}\n"
            f"expected={EXPECTED_ROWS!r}\n"
            "manifest=json.load(open('reports/manifests/offline_supervised_dataset_v2_7_manifest.json'))\n"
            "report=json.load(open('reports/datasets/offline_supervised_dataset_v2_7.json'))\n"
            "assert manifest==report\n"
            "assert manifest['version']=='V2.7'\n"
            "assert manifest['safety']['dataset_enabled'] is True\n"
            "assert manifest['safety']['labels_enabled'] is True\n"
            "assert manifest['safety']['trading_enabled'] is False\n"
            "assert manifest['safety']['ml_enabled'] is False\n"
            "assert manifest['safety']['backtest_enabled'] is False\n"
            "assert manifest['safety']['orders_enabled'] is False\n"
            "for tf,path in datasets.items():\n"
            "    df=pd.read_parquet(path)\n"
            "    assert list(df.columns)==DATASET_COLUMNS_V2_7\n"
            "    assert len(df)==expected[tf]\n"
            "print('v2.7-smoke-logical-ok')\n"
        )
        commands.append([sys.executable, "-c", script_check])

        env = os.environ.copy()
        env["PYTHONPATH"] = str(tmp_path / "src")
        for command in commands:
            try:
                completed = subprocess.run(command, cwd=tmp_path, text=True, capture_output=True, timeout=90, env=env)
            except subprocess.TimeoutExpired:
                errors.append(f"command timed out: {' '.join(command)}")
                continue
            if completed.returncode != 0:
                errors.append(f"command failed: {' '.join(command)}\nstdout={completed.stdout}\nstderr={completed.stderr}")

    payload = {
        "version": "V2.7.2",
        "zip_path": str(zip_path),
        "smoke_test_passed": not errors,
        "smoke_commands_count": len(commands),
        "smoke_failed_count": len(errors),
        "errors": errors,
    }
    Path("reports").mkdir(exist_ok=True)
    Path("reports/zip_smoke_test_v2_7_2.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path("reports/zip_smoke_test_v2_7_2.md").write_text(
        "# Smoke ZIP V2.7.2\n\n"
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
