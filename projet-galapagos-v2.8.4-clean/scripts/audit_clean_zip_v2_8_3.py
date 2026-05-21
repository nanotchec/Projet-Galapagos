from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

from release_clean_zip_v2_8_3 import FORBIDDEN_SUFFIXES, INCLUDED_PATHS, RAW_ARCHIVE_ENTRY


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
]
ALLOWED_REPORTS_ML = {
    "reports/ml/offline_ml_research_v2_8.json",
    "reports/ml/offline_ml_research_v2_8.md",
    "reports/ml/offline_research_scores_v2_8.json",
    "reports/ml/offline_research_scores_v2_8.md",
}


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
    unexpected_zips = [name for name in names if name.endswith(".zip") and name != RAW_ARCHIVE_ENTRY]
    if unexpected_zips:
        errors.append(f"unexpected nested zip found: {unexpected_zips[:5]}")
    forbidden_suffixes = [name for name in names if Path(name).suffix.casefold() in FORBIDDEN_SUFFIXES]
    if forbidden_suffixes:
        errors.append(f"forbidden model artifact found: {forbidden_suffixes[:5]}")
    unexpected_reports_ml = [name for name in names if name.startswith("reports/ml/") and name not in ALLOWED_REPORTS_ML]
    if unexpected_reports_ml:
        errors.append(f"unexpected reports/ml entry found: {unexpected_reports_ml[:5]}")
    unexpected_data_gold_ml = [
        name
        for name in names
        if name.startswith("data/gold/ml/")
        and not (name.endswith("/ml-scores-2024-01-15.parquet") and "/offline_research/" in name)
    ]
    if unexpected_data_gold_ml:
        errors.append(f"unexpected data/gold/ml entry found: {unexpected_data_gold_ml[:5]}")

    payload = {
        "version": "V2.8",
        "correction_version": "V2.8.3",
        "zip_path": str(zip_path.resolve()),
        "zip_size_bytes": zip_path.stat().st_size if zip_path.exists() else 0,
        "entries_count": len(names),
        "clean_zip_audit_passed": not errors,
        "errors": errors,
    }
    Path("reports").mkdir(exist_ok=True)
    Path("reports/zip_audit_v2_8_3.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path("reports/zip_audit_v2_8_3.md").write_text(
        "# Audit ZIP V2.8.3\n\n"
        f"- Statut : `{payload['clean_zip_audit_passed']}`\n"
        f"- Erreurs : `{len(errors)}`\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
