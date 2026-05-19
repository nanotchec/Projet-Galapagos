from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


PARQUETS_GOLD_LABELS = {
    "1m": "data/gold/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/year=2024/month=01/labels-2024-01-15.parquet",
    "5m": "data/gold/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/year=2024/month=01/labels-2024-01-15.parquet",
    "15m": "data/gold/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/year=2024/month=01/labels-2024-01-15.parquet",
    "1h": "data/gold/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/year=2024/month=01/labels-2024-01-15.parquet",
}

PARQUETS_SILVER = {
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
    
    with tempfile.TemporaryDirectory(prefix="galapagos_v2_6_smoke_") as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            archive_names = archive.namelist()
            archive.extractall(tmp_path)
            
        required = [
            "reports/manifests/clean_label_factory_v2_6_manifest.json",
            "reports/labels/clean_label_factory_v2_6.json",
            "reports/manifests/causal_feature_store_v2_5_manifest.json",
            "reports/manifests/ohlcv_resampling_v2_4_manifest.json",
            "reports/manifests/public_market_ingestion_v2_3_manifest.json",
            *PARQUETS_GOLD_LABELS.values(),
            *PARQUETS_SILVER.values(),
        ]
        for relative in required:
            if not (tmp_path / relative).exists():
                errors.append(f"missing smoke file: {relative}")
                
        # Vérification qu'aucun chemin hardcodé local n'est présent dans tests/scripts/src
        for path_entry in tmp_path.rglob("*"):
            if path_entry.is_file() and any(part in path_entry.parts for part in ["src", "scripts", "tests"]):
                if path_entry.suffix in [".py", ".json", ".md", ".toml"]:
                    try:
                        content = path_entry.read_text(encoding="utf-8", errors="ignore")
                        forbidden_pattern = "/Users/" + "lilianserre"
                        if forbidden_pattern in content:
                            errors.append(f"forbidden hardcoded local path in extracted file: {path_entry.relative_to(tmp_path)}")
                    except Exception as e:
                        errors.append(f"could not read file {path_entry.relative_to(tmp_path)}: {e}")

        # Commandes pour valider les scripts de validation individuels
        commands.append([sys.executable, "scripts/validate_public_market_ingestion_v2_3.py"])
        commands.append([sys.executable, "scripts/validate_ohlcv_resampling_v2_4.py"])
        commands.append([sys.executable, "scripts/validate_causal_feature_store_v2_5.py"])
        commands.append([sys.executable, "scripts/validate_clean_label_factory_v2_6.py"])
        
        # Commande pour exécuter les validations physiques et logiques complexes en Python pur (sans pytest)
        script_check = (
            "import json\n"
            "import pandas as pd\n"
            "from galapagos.labels.schemas import LABEL_COLUMNS_V2_6\n"
            "expected={'1m':1440,'5m':288,'15m':96,'1h':24}\n"
            f"paths_labels={PARQUETS_GOLD_LABELS!r}\n"
            "manifest_v6=json.load(open('reports/manifests/clean_label_factory_v2_6_manifest.json'))\n"
            "report_v6=json.load(open('reports/labels/clean_label_factory_v2_6.json'))\n"
            "manifest_v5=json.load(open('reports/manifests/causal_feature_store_v2_5_manifest.json'))\n"
            "manifest_v4=json.load(open('reports/manifests/ohlcv_resampling_v2_4_manifest.json'))\n"
            "manifest_v3=json.load(open('reports/manifests/public_market_ingestion_v2_3_manifest.json'))\n"
            "\n"
            "# 1. Vérification des versions de correction et structures de base\n"
            "assert manifest_v6['version']=='V2.6'\n"
            "assert manifest_v6['correction_version']=='V2.6.2'\n"
            "assert report_v6['version']=='V2.6'\n"
            "assert report_v6['correction_version']=='V2.6.2'\n"
            "assert manifest_v5['version']=='V2.5'\n"
            "assert manifest_v5['correction_version']=='V2.5.2'\n"
            "assert manifest_v4['version']=='V2.4'\n"
            "assert manifest_v4['correction_version']=='V2.4.8'\n"
            "assert manifest_v3['version']=='V2.3'\n"
            "assert manifest_v3['correction_version']=='V2.3.1'\n"
            "\n"
            "# 2. Clés inattendues\n"
            "manifest_keys={'version','correction_version','status','created_at_utc','label_run_id','input_ohlcv','outputs','label_schema_version','label_columns','horizons','threshold','quality','safety','limitations'}\n"
            "report_keys={'version','correction_version','status','created_at_utc','label_run_id','input_ohlcv','outputs','label_schema_version','label_columns','horizons','threshold','quality','safety','limitations'}\n"
            "assert set(manifest_v6)==manifest_keys\n"
            "assert set(report_v6)==report_keys\n"
            "\n"
            "# 3. Limitations exactes V2.6\n"
            "expected_limitations_v6=[\n"
            "    'V2.6 produit uniquement des labels forward separes sur BTCUSDT 2024-01-15 a partir des donnees OHLCV V2.4 validees.',\n"
            "    'V2.6 ne produit aucun dataset ML, aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.'\n"
            "]\n"
            "assert manifest_v6['limitations']==expected_limitations_v6\n"
            "assert report_v6['limitations']==expected_limitations_v6\n"
            "\n"
            "# 4. Flags de sécurité V2.6\n"
            "for payload in (manifest_v6['safety'], report_v6['safety']):\n"
            "    assert payload['trading_enabled'] is False\n"
            "    assert payload['ml_enabled'] is False\n"
            "    assert payload['labels_enabled'] is True\n"
            "    assert payload['backtest_enabled'] is False\n"
            "    assert payload['orders_enabled'] is False\n"
            "\n"
            "# 5. Lecture des Parquet Gold et validation\n"
            "for tf, path in paths_labels.items():\n"
            "    df=pd.read_parquet(path)\n"
            "    assert len(df)==expected[tf]\n"
            "    assert list(df.columns) == LABEL_COLUMNS_V2_6\n"
            "\n"
            "print('v2.6.2-smoke-logical-ok')\n"
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
                    capture_output=True, 
                    timeout=30, 
                    env=env
                )
                if completed.returncode != 0:
                    errors.append(
                        f"command failed: {' '.join(command)}\nstdout={completed.stdout}\nstderr={completed.stderr}"
                    )
            except subprocess.TimeoutExpired:
                errors.append(f"command timed out (30s): {' '.join(command)}")
            except Exception as e:
                errors.append(f"command failed with exception: {' '.join(command)}\nexception={e}")
                
        forbidden_parts = [
            ".git/",
            ".venv/",
            "__pycache__/",
            ".pytest_cache/",
            "node_modules/",
            "data/gold/datasets/",
            "data/gold/dataset_ml/",
            "reports/ml/",
            "reports/backtests/",
            "models/",
            "orders/",
            "execution/",
        ]
        for forbidden in forbidden_parts:
            if any(forbidden in name for name in archive_names):
                errors.append(f"forbidden zip entry: {forbidden}")
                
    payload = {
        "version": "V2.6",
        "correction_version": "V2.6.2",
        "zip_path": str(zip_path),
        "smoke_test_passed": not errors,
        "smoke_commands_count": len(commands),
        "smoke_failed_count": len(errors),
        "errors": errors,
    }
    
    Path("reports").mkdir(exist_ok=True)
    Path("reports/zip_smoke_test_v2_6_2.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path("reports/zip_smoke_test_v2_6_2.md").write_text(
        "# Smoke ZIP V2.6.2\n\n"
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
