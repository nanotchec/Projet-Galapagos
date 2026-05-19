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
    "1m": "data/gold/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/year=2024/month=01/features-2024-01-15.parquet",
    "5m": "data/gold/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/year=2024/month=01/features-2024-01-15.parquet",
    "15m": "data/gold/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/year=2024/month=01/features-2024-01-15.parquet",
    "1h": "data/gold/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/year=2024/month=01/features-2024-01-15.parquet",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True)
    args = parser.parse_args()
    zip_path = Path(args.zip).resolve()
    errors: list[str] = []
    commands = []
    with tempfile.TemporaryDirectory(prefix="galapagos_v2_5_1_smoke_") as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            archive_names = archive.namelist()
            archive.extractall(tmp_path)
        required = [
            "reports/manifests/causal_feature_store_v2_5_manifest.json",
            "reports/features/causal_feature_store_v2_5.json",
            *PARQUETS.values(),
        ]
        for relative in required:
            if not (tmp_path / relative).exists():
                errors.append(f"missing smoke file: {relative}")
                
        # Vérification qu'aucun chemin hardcodé local n'est présent dans tests/scripts/src
        for path_entry in tmp_path.rglob("*"):
            if path_entry.is_file() and any(part in path_entry.parts for part in ["src", "scripts", "tests"]):
                if path_entry.suffix in [".py", ".json", ".md", ".toml"]:
                    content = path_entry.read_text(encoding="utf-8", errors="ignore")
                    forbidden_pattern = "/Users/" + "lilianserre"
                    if forbidden_pattern in content:
                        errors.append(f"forbidden hardcoded local path in extracted file: {path_entry.relative_to(tmp_path)}")
                        
        commands.append([sys.executable, "scripts/validate_public_market_ingestion_v2_3.py"])
        commands.append([sys.executable, "scripts/validate_ohlcv_resampling_v2_4.py"])
        commands.append([sys.executable, "scripts/validate_causal_feature_store_v2_5.py"])
        
        # Command running dynamic validations (import schemas.py without duplicate hardcoded FEATURE_COLUMNS_V2_5)
        commands.append(
            [
                sys.executable,
                "-c",
                (
                    "import json\n"
                    "import pandas as pd\n"
                    "from galapagos.features.schemas import FEATURE_COLUMNS_V2_5\n"
                    "expected={'1m':1440,'5m':288,'15m':96,'1h':24}\n"
                    f"paths={PARQUETS!r}\n"
                    "manifest=json.load(open('reports/manifests/causal_feature_store_v2_5_manifest.json'))\n"
                    "report=json.load(open('reports/features/causal_feature_store_v2_5.json'))\n"
                    "assert manifest['version']=='V2.5'\n"
                    "assert manifest['correction_version']=='V2.5.1'\n"
                    "assert report['version']=='V2.5'\n"
                    "assert report['correction_version']=='V2.5.1'\n"
                    "manifest_keys={'version','correction_version','status','created_at_utc','feature_run_id','input_ohlcv','outputs','feature_schema_version','feature_columns','quality','public_read_only','authentication_used','api_key_used','private_endpoint_used','orders_enabled','paper_live_enabled','trading_enabled','ml_enabled','labels_enabled','backtest_enabled','limitations'}\n"
                    "report_keys={'version','correction_version','status','created_at_utc','feature_run_id','input_ohlcv','outputs','feature_schema_version','feature_columns','quality','safety','limitations'}\n"
                    "expected_limitations=['V2.5 produit uniquement des features OHLCV causales sur BTCUSDT 2024-01-15 a partir des donnees V2.4 validees.','V2.5 ne produit aucun label, aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.']\n"
                    "assert set(manifest)==manifest_keys\n"
                    "assert set(report)==report_keys\n"
                    "assert manifest['limitations']==expected_limitations\n"
                    "assert report['limitations']==expected_limitations\n"
                    "for payload in (manifest, report['safety']):\n"
                    "    assert payload['trading_enabled'] is False\n"
                    "    assert payload['ml_enabled'] is False\n"
                    "    assert payload['labels_enabled'] is False\n"
                    "    assert payload['backtest_enabled'] is False\n"
                    "    assert payload['orders_enabled'] is False\n"
                    "for tf, path in paths.items():\n"
                    "    df=pd.read_parquet(path)\n"
                    "    assert len(df)==expected[tf]\n"
                    "    assert list(df.columns) == FEATURE_COLUMNS_V2_5\n"
                    "print('v2.5.1-smoke-ok')\n"
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
        "version": "V2.5",
        "correction_version": "V2.5.1",
        "zip_path": str(zip_path),
        "smoke_test_passed": not errors,
        "smoke_commands_count": len(commands),
        "smoke_failed_count": len(errors),
        "errors": errors,
    }
    Path("reports").mkdir(exist_ok=True)
    Path("reports/zip_smoke_test_v2_5_1.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path("reports/zip_smoke_test_v2_5_1.md").write_text(
        "# Smoke ZIP V2.5.1\n\n"
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
