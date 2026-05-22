from __future__ import annotations

import argparse
import json
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any


VERSION = "V3.6"
REPORT_JSON = Path("reports/audit_lite/zip_audit_v3_6.json")
REPORT_MD = Path("reports/audit_lite/zip_audit_v3_6.md")
REQUIRED_ENTRIES = [
    "README.md",
    "pyproject.toml",
    "scripts/release_audit_lite_zip_v3_6.py",
    "scripts/audit_audit_lite_zip_v3_6.py",
    "scripts/smoke_audit_lite_zip_v3_6.py",
    "scripts/run_expanded_causal_feature_store_v3_6.py",
    "scripts/validate_expanded_causal_feature_store_v3_6.py",
    "src/galapagos/data/public_market/expanded_window.py",
    "src/galapagos/data/public_market/expanded_window_validation.py",
    "src/galapagos/features/expanded_window.py",
    "src/galapagos/features/expanded_window_validation.py",
    "src/galapagos/features/schemas.py",
    "src/galapagos/labels/__init__.py",
    "src/galapagos/datasets/__init__.py",
    "src/galapagos/ml/__init__.py",
    "tests/features/test_expanded_causal_features_v3_6.py",
    "tests/validation/test_expanded_causal_feature_store_v3_6_validator.py",
    "reports/manifests/expanded_public_market_data_v3_5_manifest.json",
    "reports/manifests/expanded_causal_feature_store_v3_6_manifest.json",
    "reports/features/expanded_causal_feature_store_v3_6.json",
    "reports/features/expanded_causal_feature_store_v3_6.md",
    "reports/audit_lite/v3_6_artifact_inventory.json",
    "reports/audit_lite/v3_6_artifact_inventory.md",
    "reports/audit_lite/v3_6_parquet_summary.json",
    "reports/audit_lite/zip_size_report_v3_6.json",
    "reports/audit_lite/zip_size_report_v3_6.md",
    "reports/PROJECT_STATE.json",
    "reports/PROJECT_STATE.md",
    "reports/current/latest_metrics.json",
    "reports/current/latest_metrics.md",
    "reports/current/latest_summary.md",
    "docs/expanded_causal_feature_store_v3_6.md",
]
SAMPLE_ENTRIES = [
    f"data/audit_lite/v3_6/features/timeframe={timeframe}/sample.parquet"
    for timeframe in ["1m", "5m", "15m", "1h"]
]
FORBIDDEN_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
FORBIDDEN_PREFIXES = [
    "data/raw/public_market/",
    "reports/backtests/",
    "reports/strategies/",
    "reports/signals/",
    "reports/predictions/",
    "orders/",
    "execution/",
    "models/",
    "checkpoints/",
]
FORBIDDEN_SUFFIXES = {".pkl", ".pickle", ".joblib", ".ckpt", ".pt", ".pth", ".onnx"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True)
    args = parser.parse_args()
    zip_path = Path(args.zip).resolve()
    errors: list[str] = []
    warnings: list[str] = []
    names: list[str] = []
    top_files: list[dict[str, Any]] = []
    zip_size = 0
    if not zip_path.exists():
        errors.append(f"zip missing: {zip_path}")
    else:
        zip_size = zip_path.stat().st_size
        try:
            with zipfile.ZipFile(zip_path) as archive:
                archive.testzip()
                infos = archive.infolist()
                names = [info.filename for info in infos]
                top_files = [
                    {"path": info.filename, "bytes": int(info.file_size)}
                    for info in sorted(infos, key=lambda item: item.file_size, reverse=True)[:20]
                ]
        except Exception as exc:  # pragma: no cover - surfaced in script output.
            errors.append(f"zip extraction/read failed: {exc}")

    name_set = set(names)
    for entry in REQUIRED_ENTRIES + SAMPLE_ENTRIES:
        if entry not in name_set:
            errors.append(f"missing required audit-lite entry: {entry}")
    errors.extend(_find_forbidden_entries(names))
    errors.extend(_validate_no_full_parquet_or_raw(names))

    if zip_path.exists() and not errors:
        with tempfile.TemporaryDirectory(prefix="galapagos_audit_lite_audit_") as tmp:
            extract_root = Path(tmp) / "extracted"
            with zipfile.ZipFile(zip_path) as archive:
                archive.extractall(extract_root)
            errors.extend(_validate_json_reports(extract_root))
            errors.extend(_validate_sample_schemas(extract_root))

    payload = {
        "version": VERSION,
        "zip_path": str(zip_path),
        "zip_size_bytes": zip_size,
        "zip_size_mb": round(zip_size / 1024 / 1024, 3),
        "entries_count": len(names),
        "audit_lite_zip_passed": not errors,
        "raw_zips_absent": not any(name.startswith("data/raw/public_market/") and name.endswith(".zip") for name in names),
        "top_20_largest_files": top_files,
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_MD.write_text(
        "# Audit ZIP audit-lite V3.6\n\n"
        f"- Statut : `{payload['audit_lite_zip_passed']}`\n"
        f"- Taille : `{payload['zip_size_mb']}` Mo\n"
        f"- Raw zips absents : `{payload['raw_zips_absent']}`\n"
        f"- Erreurs : `{len(errors)}`\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


def _find_forbidden_entries(names: list[str]) -> list[str]:
    errors: list[str] = []
    for name in names:
        path = Path(name)
        if any(part in FORBIDDEN_PARTS for part in path.parts):
            errors.append(f"forbidden cache/project entry found: {name}")
        if path.name == ".env" or "secret" in name.casefold():
            errors.append(f"forbidden secret-like entry found: {name}")
        if path.suffix.casefold() == ".zip":
            errors.append(f"forbidden nested zip found: {name}")
        if path.suffix.casefold() in FORBIDDEN_SUFFIXES:
            errors.append(f"forbidden model artifact found: {name}")
    for prefix in FORBIDDEN_PREFIXES:
        if any(name.startswith(prefix) for name in names):
            errors.append(f"forbidden prefix found: {prefix}")
    return errors


def _validate_no_full_parquet_or_raw(names: list[str]) -> list[str]:
    errors: list[str] = []
    for name in names:
        if name.endswith(".parquet") and not name.startswith("data/audit_lite/v3_6/features/"):
            errors.append(f"full parquet should not be included in audit-lite: {name}")
        if name.startswith("data/raw/public_market/"):
            errors.append(f"raw public market file should not be included in audit-lite: {name}")
    return errors


def _validate_json_reports(root: Path) -> list[str]:
    errors: list[str] = []
    inventory = _read_json(root / "reports/audit_lite/v3_6_artifact_inventory.json")
    parquet_summary = _read_json(root / "reports/audit_lite/v3_6_parquet_summary.json")
    size_report = _read_json(root / "reports/audit_lite/zip_size_report_v3_6.json")
    manifest = _read_json(root / "reports/manifests/expanded_causal_feature_store_v3_6_manifest.json")
    report = _read_json(root / "reports/features/expanded_causal_feature_store_v3_6.json")
    if inventory.get("audit_lite_does_not_replace_full_validation") is not True:
        errors.append("artifact inventory must state audit-lite does not replace full validation")
    if len(inventory.get("raw_zips_excluded", [])) != 90:
        errors.append("artifact inventory must represent 90 raw zips")
    if not parquet_summary.get("features"):
        errors.append("parquet summary must include V3.6 feature summaries")
    if size_report.get("raw_zips_excluded") is not True:
        errors.append("zip size report must mark raw zips excluded")
    if manifest != report:
        errors.append("V3.6 manifest/report mismatch in audit-lite zip")
    safety = manifest.get("safety", {})
    for flag in ["trading_enabled", "backtest_enabled", "orders_enabled", "strategy_enabled", "execution_enabled"]:
        if safety.get(flag) is not False:
            errors.append(f"unsafe V3.6 safety flag in audit-lite: {flag}")
    return errors


def _validate_sample_schemas(root: Path) -> list[str]:
    errors: list[str] = []
    sys.path.insert(0, str(root / "src"))
    from galapagos.data.public_market.storage import read_parquet
    from galapagos.features.schemas import FEATURE_COLUMNS_V3_6

    for sample in SAMPLE_ENTRIES:
        frame = read_parquet(root / sample)
        if list(frame.columns) != FEATURE_COLUMNS_V3_6:
            errors.append(f"FEATURE_COLUMNS_V3_6 mismatch for sample: {sample}")
        if len(frame) == 0:
            errors.append(f"empty audit-lite sample: {sample}")
    return errors


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
