from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

from release_clean_zip_v3_1_10 import FORBIDDEN_SUFFIXES, INCLUDED_PATHS


FORBIDDEN_PARTS = [".git/", ".venv/", "__pycache__/", ".pytest_cache/", ".ruff_cache/", ".mypy_cache/", "node_modules/"]
FORBIDDEN_PREFIXES = [
    "models/",
    "checkpoints/",
    "reports/backtests/",
    "reports/strategies/",
    "reports/signals/",
    "reports/predictions/",
    "orders/",
    "execution/",
    "data/research/v3_1/datasets/",
    "data/research/v3_1/ml/",
    "data/research/v3_1/backtests/",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True)
    args = parser.parse_args()
    zip_path = Path(args.zip)
    errors: list[str] = []
    if not zip_path.exists():
        errors.append("zip missing")
        names: list[str] = []
    else:
        with zipfile.ZipFile(zip_path) as archive:
            names = archive.namelist()
    name_set = set(names)
    for required in INCLUDED_PATHS:
        if required.endswith((".py", ".json", ".md", ".toml", ".parquet", ".zip")) and required not in name_set:
            errors.append(f"missing required entry: {required}")
    for forbidden in FORBIDDEN_PARTS:
        if any(forbidden in name for name in names):
            errors.append(f"forbidden entry found: {forbidden}")
    for prefix in FORBIDDEN_PREFIXES:
        if any(name.startswith(prefix) for name in names):
            errors.append(f"forbidden prefix found: {prefix}")
    unexpected_zips = [
        name
        for name in names
        if name.endswith(".zip") and not name.startswith("data/raw/public_market/binance_archive/spot/BTCUSDT/klines/1m/")
    ]
    if unexpected_zips:
        errors.append(f"unexpected nested zip found: {unexpected_zips[:5]}")
    forbidden_suffixes = [name for name in names if Path(name).suffix.casefold() in FORBIDDEN_SUFFIXES]
    if forbidden_suffixes:
        errors.append(f"forbidden model artifact found: {forbidden_suffixes[:5]}")
    smoke_logs = [name for name in names if Path(name).name.startswith(".smoke-")]
    if smoke_logs:
        errors.append(f"forbidden smoke log found: {smoke_logs[:5]}")
    payload = {
        "version": "V3.1.10",
        "zip_path": str(zip_path.resolve()),
        "zip_size_bytes": zip_path.stat().st_size if zip_path.exists() else 0,
        "entries_count": len(names),
        "clean_zip_audit_passed": not errors,
        "errors": errors,
    }
    Path("reports").mkdir(exist_ok=True)
    Path("reports/zip_audit_v3_1_10.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path("reports/zip_audit_v3_1_10.md").write_text(
        "# Audit ZIP V3.1.10\n\n"
        f"- Statut : `{payload['clean_zip_audit_passed']}`\n"
        f"- Erreurs : `{len(errors)}`\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
