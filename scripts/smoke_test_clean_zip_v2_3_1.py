from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


STALE_TOKENS = [
    "walk-forward",
    "walk_forward",
    "offline_walk_forward",
    "bounded_offline_walk_forward_protocol",
    "sans réseau",
    "no_network",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True)
    args = parser.parse_args()
    zip_path = Path(args.zip).resolve()
    errors: list[str] = []
    commands = []
    with tempfile.TemporaryDirectory(prefix="galapagos_v2_3_1_smoke_") as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            archive_names = archive.namelist()
            archive.extractall(tmp_path)
        checks = [
            tmp_path / "reports/manifests/public_market_ingestion_v2_3_manifest.json",
            tmp_path / "reports/PROJECT_STATE.json",
            tmp_path / "reports/current/latest_metrics.json",
            tmp_path / "data/silver/market_data/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/year=2024/month=01/part-2024-01-15.parquet",
        ]
        for path in checks:
            if not path.exists():
                errors.append(f"missing smoke file: {path.relative_to(tmp_path)}")
        commands.append([sys.executable, "scripts/validate_public_market_ingestion_v2_3.py"])
        commands.append([sys.executable, "-c", "import galapagos.data.public_market; import galapagos.validation.market_data"])
        commands.append(
            [
                sys.executable,
                "-c",
                (
                    "import json, pandas as pd; "
                    "p='data/silver/market_data/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/year=2024/month=01/part-2024-01-15.parquet'; "
                    "df=pd.read_parquet(p); "
                    "assert 'normalized_file_sha256' not in df.columns; "
                    "state=json.load(open('reports/PROJECT_STATE.json')); latest=json.load(open('reports/current/latest_metrics.json')); "
                    "fields=['authorized_future_scope','approval_phrase_expected_exact','approval_phrase_provided','candidate_scope','next_direction']; "
                    "tokens=['walk-forward','walk_forward','offline_walk_forward','bounded_offline_walk_forward_protocol','sans réseau','no_network']; "
                    "assert not any(t in str(payload.get(f, '')).lower() for payload in [state, latest] for f in fields for t in tokens); "
                    "print('v2.3.1-smoke-ok')"
                ),
            ]
        )
        env = os.environ.copy()
        env["PYTHONPATH"] = str(tmp_path / "src")
        for command in commands:
            completed = subprocess.run(command, cwd=tmp_path, text=True, capture_output=True, timeout=60, env=env)
            if completed.returncode != 0:
                errors.append(
                    f"command failed: {' '.join(command)}\nstdout={completed.stdout}\nstderr={completed.stderr}"
                )
        forbidden_parts = [".git/", ".venv/", "__pycache__/", ".pytest_cache/", "node_modules/"]
        for forbidden in forbidden_parts:
            if any(forbidden in name for name in archive_names):
                errors.append(f"forbidden zip entry: {forbidden}")
    payload = {
        "version": "V2.3.1",
        "zip_path": str(zip_path),
        "smoke_test_passed": not errors,
        "smoke_commands_count": len(commands),
        "smoke_failed_count": len(errors),
        "bounded_smoke_for_v2_3_1": True,
        "errors": errors,
    }
    Path("reports").mkdir(exist_ok=True)
    Path("reports/zip_smoke_test_v2_3_1.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path("reports/zip_smoke_test_v2_3_1.md").write_text(
        "# Smoke ZIP V2.3.1\n\n"
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
