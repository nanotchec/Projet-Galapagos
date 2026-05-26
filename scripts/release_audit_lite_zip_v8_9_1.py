from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.data.public_market.provenance import sha256_file
from galapagos.features.ohlcv_trades_feature_selection_schemas import (
    ARTIFACT_INVENTORY_JSON_V8_9,
    ARTIFACT_INVENTORY_MD_V8_9,
    ATTESTATION_JSON_V8_9,
    ATTESTATION_MD_V8_9,
    COMMAND_TIMINGS_JSON_V8_9,
    DOC_PATH_V8_9,
    INPUT_DATASET_MANIFEST_PATH_V8_9,
    INPUT_DECISION_JSON_PATH_V8_9,
    INPUT_DECISION_MD_PATH_V8_9,
    INPUT_FEATURE_MANIFEST_PATH_V8_9,
    INPUT_FEATURE_REPORT_PATH_V8_9,
    INPUT_ML_MANIFEST_PATH_V8_9,
    INPUT_ML_REPORT_PATH_V8_9,
    INPUT_WALK_FORWARD_MANIFEST_PATH_V8_9,
    INPUT_WALK_FORWARD_REPORT_PATH_V8_9,
    MANIFEST_PATH_V8_9,
    REPORT_JSON_PATH_V8_9,
    REPORT_MD_PATH_V8_9,
    SELECTION_JSON_PATH_V8_9,
    SELECTION_MD_PATH_V8_9,
    ZIP_SIZE_JSON_V8_9,
    ZIP_SIZE_MD_V8_9,
)


VERSION = "V8.9.1"
ZIP_NAME = "projet-galapagos-v8.9.1-audit-lite.zip"
ZIP_SIZE_JSON = Path("reports/audit_lite/zip_size_report_v8_9_1.json")
ZIP_SIZE_MD = Path("reports/audit_lite/zip_size_report_v8_9_1.md")
SOURCE_PREFIXES = [
    Path("src/galapagos/data/public_market"),
    Path("src/galapagos/data/public_trades"),
    Path("src/galapagos/datasets"),
    Path("src/galapagos/features"),
    Path("src/galapagos/labels"),
    Path("src/galapagos/ml"),
    Path("src/galapagos/validation"),
]
SOURCE_EXACT = [Path("src/galapagos/__init__.py"), Path("src/galapagos/data/__init__.py")]
SCRIPT_EXACT = [
    Path("scripts/_bootstrap.py"),
    Path("scripts/run_ohlcv_trades_feature_audit_v8_9.py"),
    Path("scripts/validate_ohlcv_trades_feature_audit_v8_9.py"),
    Path("scripts/release_audit_lite_zip_v8_9.py"),
    Path("scripts/audit_audit_lite_zip_v8_9.py"),
    Path("scripts/smoke_audit_lite_zip_v8_9.py"),
    Path("scripts/release_audit_lite_zip_v8_9_1.py"),
    Path("scripts/audit_audit_lite_zip_v8_9_1.py"),
    Path("scripts/smoke_audit_lite_zip_v8_9_1.py"),
]
TEST_EXACT = [
    Path("tests/features/test_ohlcv_trades_feature_audit_v8_9.py"),
    Path("tests/validation/test_ohlcv_trades_feature_audit_v8_9_validator.py"),
]
LIGHTWEIGHT_INPUTS = [
    INPUT_DATASET_MANIFEST_PATH_V8_9,
    Path("reports/datasets/ohlcv_trades_1y_offline_supervised_dataset_v8_4.json"),
    INPUT_FEATURE_MANIFEST_PATH_V8_9,
    INPUT_FEATURE_REPORT_PATH_V8_9,
    INPUT_ML_MANIFEST_PATH_V8_9,
    INPUT_ML_REPORT_PATH_V8_9,
    INPUT_WALK_FORWARD_MANIFEST_PATH_V8_9,
    INPUT_WALK_FORWARD_REPORT_PATH_V8_9,
    INPUT_DECISION_JSON_PATH_V8_9,
    INPUT_DECISION_MD_PATH_V8_9,
]
REPORT_EXACT = [
    MANIFEST_PATH_V8_9,
    REPORT_JSON_PATH_V8_9,
    REPORT_MD_PATH_V8_9,
    SELECTION_JSON_PATH_V8_9,
    SELECTION_MD_PATH_V8_9,
    DOC_PATH_V8_9,
    ARTIFACT_INVENTORY_JSON_V8_9,
    ARTIFACT_INVENTORY_MD_V8_9,
    ATTESTATION_JSON_V8_9,
    ATTESTATION_MD_V8_9,
    ZIP_SIZE_JSON_V8_9,
    ZIP_SIZE_MD_V8_9,
    COMMAND_TIMINGS_JSON_V8_9,
    *LIGHTWEIGHT_INPUTS,
    Path("reports/PROJECT_STATE.json"),
    Path("reports/PROJECT_STATE.md"),
    Path("reports/current/latest_metrics.json"),
    Path("reports/current/latest_metrics.md"),
    Path("reports/current/latest_summary.md"),
    Path("README.md"),
    Path("pyproject.toml"),
]
FORBIDDEN_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo", ".pkl", ".pickle", ".joblib", ".ckpt", ".pt", ".pth", ".onnx", ".zip"}
FORBIDDEN_PREFIXES = [
    "data/raw/",
    "data/research/",
    "reports/backtests/",
    "reports/strategies/",
    "reports/signals/",
    "reports/predictions/",
    "orders/",
    "execution/",
    "models/",
    "checkpoints/",
]


def main() -> None:
    root = Path(".").resolve()
    manifest = _read_json(root / MANIFEST_PATH_V8_9)
    report = _read_json(root / REPORT_JSON_PATH_V8_9)
    selection = _read_json(root / SELECTION_JSON_PATH_V8_9)
    if manifest != report:
        raise RuntimeError("V8.9 manifest and feature audit report JSON must match before V8.9.1 release.")
    if selection["candidate_refined_feature_set"] != manifest["candidate_refined_feature_set"]:
        raise RuntimeError("V8.9 selection report must match manifest before V8.9.1 release.")
    for relative in LIGHTWEIGHT_INPUTS:
        if relative in [INPUT_WALK_FORWARD_MANIFEST_PATH_V8_9, INPUT_WALK_FORWARD_REPORT_PATH_V8_9, INPUT_DECISION_MD_PATH_V8_9]:
            continue
        if not (root / relative).exists():
            raise RuntimeError(f"missing required lightweight input for V8.9.1: {relative}")
    zip_path = root / ZIP_NAME
    included = _collect_files(root)
    zip_size_bytes = zip_path.stat().st_size if zip_path.exists() else 0
    for _attempt in range(8):
        included = _collect_files(root)
        _write_zip(root, zip_path, included)
        current_size = zip_path.stat().st_size
        if current_size == zip_size_bytes:
            break
        zip_size_bytes = current_size
    _write_size_report(root, zip_path.stat().st_size, included)
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": "PASS",
                "zip_path": str(zip_path),
                "zip_size_bytes": zip_path.stat().st_size,
                "files_included": len(included),
                "lightweight_inputs_included": [path.as_posix() for path in LIGHTWEIGHT_INPUTS if (root / path).exists()],
                "raw_zips_excluded": True,
                "full_parquet_excluded": True,
                "functional_v8_9_results_unchanged": True,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


def _collect_files(root: Path) -> list[Path]:
    files: set[Path] = set()
    for prefix in SOURCE_PREFIXES:
        if (root / prefix).exists():
            files.update(path.relative_to(root) for path in (root / prefix).rglob("*.py") if _include_file(path.relative_to(root)))
    for path in [*SOURCE_EXACT, *SCRIPT_EXACT, *TEST_EXACT, *REPORT_EXACT]:
        if (root / path).exists() and _include_file(path):
            files.add(path)
    return sorted(files, key=lambda path: path.as_posix())


def _include_file(path: Path) -> bool:
    text = path.as_posix()
    if any(part in FORBIDDEN_PARTS for part in path.parts):
        return False
    if any(text.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
        return False
    if path.suffix.casefold() in FORBIDDEN_SUFFIXES:
        return False
    return True


def _write_zip(root: Path, zip_path: Path, files: list[Path]) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative in files:
            archive.write(root / relative, relative.as_posix())


def _write_size_report(root: Path, zip_size_bytes: int, included: list[Path]) -> None:
    payload: dict[str, Any] = {
        "version": VERSION,
        "zip_size_bytes": int(zip_size_bytes),
        "zip_size_mb": round(zip_size_bytes / 1024 / 1024, 3) if zip_size_bytes else 0,
        "included_files": len(included),
        "lightweight_inputs_included": [path.as_posix() for path in LIGHTWEIGHT_INPUTS if (root / path).exists()],
        "v8_9_manifest_sha256": sha256_file(root / MANIFEST_PATH_V8_9),
        "v8_9_report_sha256": sha256_file(root / REPORT_JSON_PATH_V8_9),
        "v8_9_selection_sha256": sha256_file(root / SELECTION_JSON_PATH_V8_9),
        "audit_lite_does_not_replace_full_validation": True,
        "raw_zips_excluded": True,
        "full_parquet_excluded": True,
        "functional_v8_9_results_unchanged": True,
    }
    _write_json(root / ZIP_SIZE_JSON, payload)
    _write_text(
        root / ZIP_SIZE_MD,
        "\n".join(
            [
                "# Taille ZIP audit-lite V8.9.1",
                "",
                f"- Taille : `{payload['zip_size_bytes']}` octets.",
                f"- Fichiers inclus : `{payload['included_files']}`.",
                "- Correctif : inclusion des petits manifests/reports d'entree necessaires aux tests nominaux.",
                "- Raw zips et gros Parquet exclus.",
            ]
        )
        + "\n",
    )


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
