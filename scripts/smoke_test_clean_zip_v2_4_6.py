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
    with tempfile.TemporaryDirectory(prefix="galapagos_v2_4_6_smoke_") as tmp:
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
        
        # Command running dynamic validations (import schemas.py without duplicate hardcoded OHLCV_COLUMNS)
        commands.append(
            [
                sys.executable,
                "-c",
                (
                    "import json\n"
                    "import pandas as pd\n"
                    "from galapagos.data.public_market.schemas import OHLCV_COLUMNS\n"
                    "expected={'1m':1440,'5m':288,'15m':96,'1h':24}\n"
                    f"paths={PARQUETS!r}\n"
                    "manifest=json.load(open('reports/manifests/ohlcv_resampling_v2_4_manifest.json'))\n"
                    "report=json.load(open('reports/data_quality/ohlcv_resampling_v2_4.json'))\n"
                    "ing_manifest=json.load(open('reports/manifests/public_market_ingestion_v2_3_manifest.json'))\n"
                    "ing_report=json.load(open('reports/data_quality/public_market_ingestion_v2_3.json'))\n"
                    "assert manifest['correction_version']=='V2.4.6'\n"
                    "assert report['correction_version']=='V2.4.6'\n"
                    "manifest_keys={'version','correction_version','status','created_at_utc','resampling_run_id','input_1m','outputs','expected_rows','quality','parent_child_consistency','public_read_only','authentication_used','api_key_used','private_endpoint_used','orders_enabled','paper_live_enabled','trading_enabled','ml_enabled','labels_enabled','backtest_enabled','limitations'}\n"
                    "report_keys={'version','correction_version','status','created_at_utc','resampling_run_id','input_1m','outputs','expected_rows','quality','parent_child_consistency','safety','limitations'}\n"
                    "ing_manifest_keys={'version','correction_version','mission','status','created_at_utc','ingestion_run_id','network_used','public_read_only','authentication_used','api_key_used','private_endpoint_used','orders_enabled','paper_live_enabled','trading_enabled','ml_enabled','labels_enabled','backtest_enabled','source','raw','silver','quality','limitations'}\n"
                    "ing_report_keys={'version','correction_version','status','created_at_utc','ingestion_run_id','source_url','source','quality','raw_checksum','silver_checksum','raw_path','silver_path','safety','limitations'}\n"
                    "expected_limitations=['V2.4 resample uniquement BTCUSDT 2024-01-15 depuis le silver 1m valide V2.3.1.','V2.4 est data-only : aucun signal, aucun label, aucun ML, aucun backtest et aucun trading.']\n"
                    "expected_ing_limitations=['V2.3 couvre une seule source publique read-only, un seul symbole, un seul timeframe et une seule journee.','V2.3 ne valide aucune strategie, aucun modele ML, aucun signal, aucun backtest et aucun trading.']\n"
                    "assert set(manifest)==manifest_keys\n"
                    "assert set(report)==report_keys\n"
                    "assert set(ing_manifest)==ing_manifest_keys\n"
                    "assert set(ing_report)==ing_report_keys\n"
                    "assert manifest['limitations']==expected_limitations\n"
                    "assert report['limitations']==expected_limitations\n"
                    "assert ing_manifest['limitations']==expected_ing_limitations\n"
                    "assert ing_report['limitations']==expected_ing_limitations\n"
                    "for payload in (manifest, report['safety']):\n"
                    "    assert payload['trading_enabled'] is False\n"
                    "    assert payload['ml_enabled'] is False\n"
                    "    assert payload['labels_enabled'] is False\n"
                    "    assert payload['backtest_enabled'] is False\n"
                    "    assert payload['orders_enabled'] is False\n"
                    "for tf, path in paths.items():\n"
                    "    df=pd.read_parquet(path)\n"
                    "    assert len(df)==expected[tf]\n"
                    "    assert list(df.columns) == OHLCV_COLUMNS\n"
                    "    assert 'normalized_file_sha256' not in df.columns\n"
                      "print('v2.4.6-smoke-ok')\n"
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
        "version": "V2.4.6",
        "resampling_artifact_version": "V2.4",
        "zip_path": str(zip_path),
        "smoke_test_passed": not errors,
        "smoke_commands_count": len(commands),
        "smoke_failed_count": len(errors),
        "bounded_smoke_for_v2_4_6": True,
        "errors": errors,
    }
    Path("reports").mkdir(exist_ok=True)
    Path("reports/zip_smoke_test_v2_4_6.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path("reports/zip_smoke_test_v2_4_6.md").write_text(
        "# Smoke ZIP V2.4.6\n\n"
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
