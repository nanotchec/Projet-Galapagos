from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

from release_clean_zip_v2_7_1 import INCLUDED_PATHS, RAW_ARCHIVE_ENTRY


FORBIDDEN_PARTS = [".git/", ".venv/", "__pycache__/", ".pytest_cache/", ".ruff_cache/", ".mypy_cache/", "node_modules/"]
FORBIDDEN_PREFIXES = ["models/", "reports/ml/", "reports/backtests/", "reports/strategies/", "reports/signals/", "reports/predictions/", "orders/", "execution/"]


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

    for required in INCLUDED_PATHS:
        if required.endswith(".py") or required.endswith(".json") or required.endswith(".md") or required.endswith(".toml") or required.endswith(".parquet") or required.endswith(".zip"):
            if required not in names:
                errors.append(f"missing required entry: {required}")
    for forbidden in FORBIDDEN_PARTS:
        if any(forbidden in name for name in names):
            errors.append(f"forbidden entry found: {forbidden}")
    for prefix in FORBIDDEN_PREFIXES:
        if any(name.startswith(prefix) for name in names):
            errors.append(f"forbidden prefix found: {prefix}")
    unexpected_zips = [name for name in names if name.endswith(".zip") and name != RAW_ARCHIVE_ENTRY]
    if unexpected_zips:
        errors.append(f"unexpected nested zip found: {unexpected_zips[:5]}")

    payload = {
        "version": "V2.7.1",
        "zip_path": str(zip_path.resolve()),
        "zip_size_bytes": zip_path.stat().st_size if zip_path.exists() else 0,
        "entries_count": len(names),
        "clean_zip_audit_passed": not errors,
        "errors": errors,
    }
    Path("reports").mkdir(exist_ok=True)
    Path("reports/zip_audit_v2_7_1.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path("reports/zip_audit_v2_7_1.md").write_text(
        "# Audit ZIP V2.7.1\n\n"
        f"- Statut : `{payload['clean_zip_audit_passed']}`\n"
        f"- Erreurs : `{len(errors)}`\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
