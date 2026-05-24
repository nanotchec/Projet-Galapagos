from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from typing import Any


VERSION = "V5.4"
AUDIT_JSON = Path("reports/audit_lite/zip_audit_v5_4.json")
AUDIT_MD = Path("reports/audit_lite/zip_audit_v5_4.md")
REQUIRED_ENTRIES = {
    "reports/manifests/max_history_offline_ml_research_v5_4_manifest.json",
    "reports/ml/max_history_offline_ml_research_v5_4.json",
    "reports/ml/max_history_offline_ml_research_v5_4.md",
    "reports/ml/max_history_offline_research_scores_v5_4.json",
    "reports/ml/max_history_offline_research_scores_v5_4.md",
    "reports/audit_lite/v5_4_artifact_inventory.json",
    "reports/audit_lite/v5_4_parquet_summary.json",
    "reports/audit_lite/v5_4_full_local_validation_attestation.json",
    "docs/max_history_offline_ml_research_v5_4.md",
    "reports/PROJECT_STATE.json",
    "reports/current/latest_summary.md",
}
FORBIDDEN_PREFIXES = (
    "data/raw/",
    "data/research/",
    "reports/backtests/",
    "reports/strategies/",
    "orders/",
    "execution/",
    "models/",
    "checkpoints/",
)
FORBIDDEN_SUFFIXES = (".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt")


def audit_zip(zip_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not zip_path.exists():
        return _result(zip_path, 0, [], [f"missing zip: {zip_path}"], warnings)
    with zipfile.ZipFile(zip_path) as archive:
        entries = sorted(archive.namelist())
        entry_set = set(entries)
    missing = sorted(REQUIRED_ENTRIES - entry_set)
    if missing:
        errors.extend(f"missing required entry: {entry}" for entry in missing)
    forbidden = [
        entry
        for entry in entries
        if entry.startswith(FORBIDDEN_PREFIXES)
        or entry.endswith(FORBIDDEN_SUFFIXES)
        or (entry.endswith(".parquet") and not entry.startswith("data/audit_lite/v5_4/ml_scores/"))
    ]
    if forbidden:
        errors.extend(f"forbidden zip entry: {entry}" for entry in forbidden)
    sample_count = sum(1 for entry in entries if entry.startswith("data/audit_lite/v5_4/ml_scores/") and entry.endswith("/sample.parquet"))
    if sample_count != 4:
        errors.append(f"expected 4 V5.4 score samples, found {sample_count}")
    return _result(zip_path, zip_path.stat().st_size, entries, errors, warnings)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True, dest="zip_path")
    args = parser.parse_args()
    result = audit_zip(Path(args.zip_path).resolve())
    _write_reports(result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not result["passed"]:
        raise SystemExit(1)


def _result(zip_path: Path, size: int, entries: list[str], errors: list[str], warnings: list[str]) -> dict[str, Any]:
    largest = []
    if zip_path.exists():
        with zipfile.ZipFile(zip_path) as archive:
            largest = sorted(
                [{"path": item.filename, "bytes": item.file_size} for item in archive.infolist()],
                key=lambda item: item["bytes"],
                reverse=True,
            )[:20]
    return {
        "version": VERSION,
        "zip_path": str(zip_path),
        "zip_size_bytes": int(size),
        "zip_size_mb": round(size / 1024 / 1024, 3) if size else 0,
        "entries": len(entries),
        "top_20_largest_files": largest,
        "raw_zips_absent": not any(entry.startswith("data/raw/") for entry in entries),
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def _write_reports(result: dict[str, Any]) -> None:
    AUDIT_JSON.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Audit ZIP V5.4",
        "",
        f"- ZIP : `{result['zip_path']}`.",
        f"- Taille : `{result['zip_size_bytes']}` octets.",
        f"- Entrees : `{result['entries']}`.",
        f"- Resultat : `{'PASS' if result['passed'] else 'FAIL'}`.",
        f"- Erreurs : `{len(result['errors'])}`.",
    ]
    AUDIT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
