from __future__ import annotations

import argparse
import importlib
import json
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Any


VERSION = "V3.7"
REPORT_JSON = Path("reports/audit_lite/zip_smoke_v3_7.json")
REPORT_MD = Path("reports/audit_lite/zip_smoke_v3_7.md")
SAMPLE_ENTRIES = [f"data/audit_lite/v3_7/labels/timeframe={timeframe}/sample.parquet" for timeframe in ["1m", "5m", "15m", "1h"]]
MODULES_TO_IMPORT = [
    "galapagos.data.public_market.expanded_window",
    "galapagos.features.expanded_window",
    "galapagos.labels.expanded_window",
    "galapagos.labels.expanded_window_validation",
    "galapagos.labels.schemas",
    "galapagos.datasets",
    "galapagos.ml",
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
    "data/research/v3_7/datasets/",
    "data/research/v3_7/ml/",
    "data/research/v3_7/backtests/",
]
FORBIDDEN_SUFFIXES = {".pkl", ".pickle", ".joblib", ".ckpt", ".pt", ".pth", ".onnx"}


def main() -> None:
    started = time.perf_counter()
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True)
    args = parser.parse_args()
    zip_path = Path(args.zip).resolve()
    errors: list[str] = []
    sample_rows: dict[str, int] = {}
    with tempfile.TemporaryDirectory(prefix="galapagos_v3_7_audit_lite_smoke_") as tmp:
        root = Path(tmp) / "extracted"
        with zipfile.ZipFile(zip_path) as archive:
            names = archive.namelist()
            archive.extractall(root)
        errors.extend(_find_forbidden_entries(names))
        sys.path.insert(0, str(root / "src"))
        errors.extend(_validate_imports())
        report_errors, sample_rows = _validate_reports_and_samples(root)
        errors.extend(report_errors)
    duration = round(time.perf_counter() - started, 3)
    payload = {
        "version": VERSION,
        "zip_path": str(zip_path),
        "smoke_passed": not errors,
        "raw_zips_absent": True,
        "full_validation_replaced": False,
        "full_validation_note": "audit-lite does not replace full local validation",
        "sample_rows": sample_rows,
        "smoke_duration_seconds": duration,
        "errors": errors,
        "warnings": [],
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_MD.write_text(
        "# Smoke ZIP audit-lite V3.7\n\n"
        f"- Statut : `{payload['smoke_passed']}`\n"
        f"- Duree : `{payload['smoke_duration_seconds']}` secondes\n"
        "- Validation full remplacee : `false`\n"
        f"- Erreurs : `{len(errors)}`\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


def _validate_imports() -> list[str]:
    errors: list[str] = []
    for module_name in MODULES_TO_IMPORT:
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            errors.append(f"import failed for {module_name}: {exc}")
    return errors


def _validate_reports_and_samples(root: Path) -> tuple[list[str], dict[str, int]]:
    from galapagos.data.public_market.storage import read_parquet
    from galapagos.labels.schemas import LABEL_COLUMNS_V3_7

    errors: list[str] = []
    sample_rows: dict[str, int] = {}
    manifest = _read_json(root / "reports/manifests/expanded_label_factory_v3_7_manifest.json")
    report = _read_json(root / "reports/labels/expanded_label_factory_v3_7.json")
    parquet_summary = _read_json(root / "reports/audit_lite/v3_7_parquet_summary.json")
    artifact_inventory = _read_json(root / "reports/audit_lite/v3_7_artifact_inventory.json")
    attestation = _read_json(root / "reports/audit_lite/v3_7_full_local_validation_attestation.json")
    project_state = _read_json(root / "reports/PROJECT_STATE.json")
    if manifest != report:
        errors.append("V3.7 manifest and report differ in audit-lite smoke")
    if manifest.get("version") != VERSION or manifest.get("status") != "PASS":
        errors.append("V3.7 manifest must be PASS")
    if project_state.get("candidate_version") != VERSION:
        errors.append("PROJECT_STATE must identify V3.7 candidate")
    if artifact_inventory.get("audit_lite_does_not_replace_full_validation") is not True:
        errors.append("audit-lite inventory must not replace full validation")
    if len(artifact_inventory.get("raw_zips_excluded", [])) != 90:
        errors.append("audit-lite inventory must represent 90 raw zips")
    if attestation.get("validation_scope") != "full_local":
        errors.append("full local attestation must use validation_scope=full_local")
    if attestation.get("audit_lite_does_not_replace_full_local_validation") is not True:
        errors.append("full local attestation must state audit-lite does not replace full validation")
    for flag in ["tests_passed", "validator_passed", "audit_lite_passed", "smoke_audit_lite_passed", "no_trading", "no_backtest", "no_orders"]:
        if attestation.get(flag) is not True:
            errors.append(f"full local attestation flag must be true: {flag}")
    if parquet_summary.get("label_schema") != "LABEL_COLUMNS_V3_7":
        errors.append("parquet summary must identify LABEL_COLUMNS_V3_7")
    for timeframe, summary in parquet_summary.get("labels", {}).items():
        if summary.get("schema_strict") is not True:
            errors.append(f"parquet summary schema is not strict for {timeframe}")
        if summary.get("forbidden_columns_present"):
            errors.append(f"forbidden columns reported for {timeframe}: {summary['forbidden_columns_present']}")
    safety = manifest.get("safety", {})
    for flag in ["trading_enabled", "backtest_enabled", "orders_enabled", "strategy_enabled", "execution_enabled", "ml_enabled", "dataset_enabled"]:
        if safety.get(flag) is not False:
            errors.append(f"unsafe V3.7 flag active: {flag}")
    for sample in SAMPLE_ENTRIES:
        frame = read_parquet(root / sample)
        timeframe = Path(sample).parent.name.removeprefix("timeframe=")
        sample_rows[timeframe] = int(len(frame))
        if list(frame.columns) != LABEL_COLUMNS_V3_7:
            errors.append(f"LABEL_COLUMNS_V3_7 mismatch for {sample}")
        if len(frame) < 100:
            errors.append(f"audit-lite sample too small for {sample}")
    return errors, sample_rows


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
        if name.endswith(".parquet") and not name.startswith("data/audit_lite/v3_7/labels/"):
            errors.append(f"full parquet should not be included in audit-lite: {name}")
    for prefix in FORBIDDEN_PREFIXES:
        if any(name.startswith(prefix) for name in names):
            errors.append(f"forbidden prefix found: {prefix}")
    return errors


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
