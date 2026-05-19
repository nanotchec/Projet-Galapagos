from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


PARQUETS = {
    "1m": "data/silver/market_data/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/year=2024/month=01/part-2024-01-15.parquet",
    "5m": "data/silver/market_data/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/year=2024/month=01/part-2024-01-15.parquet",
    "15m": "data/silver/market_data/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/year=2024/month=01/part-2024-01-15.parquet",
    "1h": "data/silver/market_data/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/year=2024/month=01/part-2024-01-15.parquet",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True)
    args = parser.parse_args()
    zip_path = Path(args.zip).resolve()
    errors: list[str] = []
    commands = []
    with tempfile.TemporaryDirectory(prefix="galapagos_v2_4_smoke_") as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            archive_names = archive.namelist()
            archive.extractall(tmp_path)
        required = [
            "reports/manifests/ohlcv_resampling_v2_4_manifest.json",
            "reports/data_quality/ohlcv_resampling_v2_4.json",
            *PARQUETS.values(),
        ]
        for relative in required:
            if not (tmp_path / relative).exists():
                errors.append(f"missing smoke file: {relative}")
        commands.append([sys.executable, "scripts/validate_public_market_ingestion_v2_3.py"])
        commands.append([sys.executable, "scripts/validate_ohlcv_resampling_v2_4.py"])
        commands.append(
            [
                sys.executable,
                "-c",
                (
                    "import json\n"
                    "import pandas as pd\n"
                    "expected={'1m':1440,'5m':288,'15m':96,'1h':24}\n"
                    f"paths={PARQUETS!r}\n"
                    "manifest=json.load(open('reports/manifests/ohlcv_resampling_v2_4_manifest.json'))\n"
                    "assert manifest['trading_enabled'] is False\n"
                    "assert manifest['ml_enabled'] is False\n"
                    "assert manifest['labels_enabled'] is False\n"
                    "assert manifest['backtest_enabled'] is False\n"
                    "assert manifest['orders_enabled'] is False\n"
                    "for tf, path in paths.items():\n"
                    "    df=pd.read_parquet(path)\n"
                    "    assert len(df)==expected[tf]\n"
                    "    assert 'normalized_file_sha256' not in df.columns\n"
                    "print('v2.4-smoke-ok')\n"
                ),
            ]
        )
        env = os.environ.copy()
        env["PYTHONPATH"] = str(tmp_path / "src")
        for command in commands:
            completed = subprocess.run(command, cwd=tmp_path, text=True, capture_output=True, timeout=90, env=env)
            if completed.returncode != 0:
                errors.append(
                    f"command failed: {' '.join(command)}\nstdout={completed.stdout}\nstderr={completed.stderr}"
                )
        forbidden_parts = [".git/", ".venv/", "__pycache__/", ".pytest_cache/", "node_modules/"]
        for forbidden in forbidden_parts:
            if any(forbidden in name for name in archive_names):
                errors.append(f"forbidden zip entry: {forbidden}")
    payload = {
        "version": "V2.4",
        "zip_path": str(zip_path),
        "smoke_test_passed": not errors,
        "smoke_commands_count": len(commands),
        "smoke_failed_count": len(errors),
        "bounded_smoke_for_v2_4": True,
        "errors": errors,
    }
    Path("reports").mkdir(exist_ok=True)
    Path("reports/zip_smoke_test_v2_4.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path("reports/zip_smoke_test_v2_4.md").write_text(
        "# Smoke ZIP V2.4\n\n"
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
