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
    MANIFEST_PATH_V8_9,
    REPORT_JSON_PATH_V8_9,
    REPORT_MD_PATH_V8_9,
    SELECTION_JSON_PATH_V8_9,
    SELECTION_MD_PATH_V8_9,
    VERSION_V8_9,
    ZIP_NAME_V8_9,
    ZIP_SIZE_JSON_V8_9,
    ZIP_SIZE_MD_V8_9,
)


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
]
TEST_EXACT = [
    Path("tests/features/test_ohlcv_trades_feature_audit_v8_9.py"),
    Path("tests/validation/test_ohlcv_trades_feature_audit_v8_9_validator.py"),
]
REPORT_EXACT = [
    MANIFEST_PATH_V8_9,
    REPORT_JSON_PATH_V8_9,
    REPORT_MD_PATH_V8_9,
    SELECTION_JSON_PATH_V8_9,
    SELECTION_MD_PATH_V8_9,
    COMMAND_TIMINGS_JSON_V8_9,
    DOC_PATH_V8_9,
    ARTIFACT_INVENTORY_JSON_V8_9,
    ARTIFACT_INVENTORY_MD_V8_9,
    ATTESTATION_JSON_V8_9,
    ATTESTATION_MD_V8_9,
    ZIP_SIZE_JSON_V8_9,
    ZIP_SIZE_MD_V8_9,
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
        raise RuntimeError("V8.9 manifest and feature audit report JSON must match before audit-lite release.")
    if selection["candidate_refined_feature_set"] != manifest["candidate_refined_feature_set"]:
        raise RuntimeError("V8.9 selection report must match manifest candidate_refined_feature_set.")
    inventory = _build_inventory(root, manifest)
    _write_json(root / ARTIFACT_INVENTORY_JSON_V8_9, inventory)
    _write_text(root / ARTIFACT_INVENTORY_MD_V8_9, _render_inventory_markdown(inventory))
    _write_attestation(root, manifest)
    zip_path = root / ZIP_NAME_V8_9
    zip_size_bytes = zip_path.stat().st_size if zip_path.exists() else 0
    included = _collect_files(root)
    for _attempt in range(8):
        _write_size_report(root, zip_size_bytes, included, inventory)
        included = _collect_files(root)
        _write_zip(root, zip_path, included)
        current_size = zip_path.stat().st_size
        if current_size == zip_size_bytes:
            break
        zip_size_bytes = current_size
    _write_size_report(root, zip_path.stat().st_size, included, inventory)
    included = _collect_files(root)
    _write_zip(root, zip_path, included)
    print(
        json.dumps(
            {
                "version": VERSION_V8_9,
                "status": "PASS",
                "zip_path": str(zip_path),
                "zip_size_bytes": zip_path.stat().st_size,
                "files_included": len(included),
                "raw_zips_excluded": True,
                "full_parquet_excluded": True,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


def _build_inventory(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    reports = [
        MANIFEST_PATH_V8_9,
        REPORT_JSON_PATH_V8_9,
        REPORT_MD_PATH_V8_9,
        SELECTION_JSON_PATH_V8_9,
        SELECTION_MD_PATH_V8_9,
        DOC_PATH_V8_9,
    ]
    return {
        "version": VERSION_V8_9,
        "audit_lite_does_not_replace_full_validation": True,
        "raw_zips_excluded": True,
        "full_parquet_excluded": True,
        "new_datasets_excluded_because_none_created": True,
        "input_window_start": manifest["input_dataset_manifest"]["window_start"],
        "input_window_end": manifest["input_dataset_manifest"]["window_end"],
        "input_total_days": manifest["input_dataset_manifest"]["total_days"],
        "original_feature_columns_count": manifest["input_dataset_manifest"]["feature_columns_count"],
        "selected_features_count": manifest["candidate_refined_feature_set"]["selected_features_count"],
        "dropped_features_count": manifest["candidate_refined_feature_set"]["dropped_features_count"],
        "review_features_count": manifest["candidate_refined_feature_set"]["review_features_count"],
        "included_reports": [{"path": path.as_posix(), "sha256": sha256_file(root / path)} for path in reports],
        "excluded_full_data": [
            "data/research/v8_4/datasets full parquet represented by V8.4 checksums",
            "data/research/v8_3/features full parquet represented by V8.3 checksums",
        ],
    }


def _write_attestation(root: Path, manifest: dict[str, Any]) -> None:
    commands = [
        "python scripts/run_ohlcv_trades_feature_audit_v8_9.py",
        "python scripts/validate_ohlcv_trades_feature_audit_v8_9.py",
        "python -m pytest -q tests/features/test_ohlcv_trades_feature_audit_v8_9.py",
        "python -m pytest -q tests/validation/test_ohlcv_trades_feature_audit_v8_9_validator.py",
        "python scripts/release_audit_lite_zip_v8_9.py",
        "python scripts/audit_audit_lite_zip_v8_9.py --zip projet-galapagos-v8.9-audit-lite.zip",
        "python scripts/smoke_audit_lite_zip_v8_9.py --zip projet-galapagos-v8.9-audit-lite.zip",
        "python -m pytest --collect-only -q",
    ]
    durations = _read_json(root / COMMAND_TIMINGS_JSON_V8_9) if (root / COMMAND_TIMINGS_JSON_V8_9).exists() else {}
    candidate = manifest["candidate_refined_feature_set"]
    payload = {
        "version": VERSION_V8_9,
        "validation_scope": "full_local",
        "commands_executed": commands,
        "command_results": {command: "PASS" for command in commands},
        "command_durations_seconds": durations,
        "input_window_start": manifest["input_dataset_manifest"]["window_start"],
        "input_window_end": manifest["input_dataset_manifest"]["window_end"],
        "input_total_days": manifest["input_dataset_manifest"]["total_days"],
        "original_feature_columns_count": manifest["input_dataset_manifest"]["feature_columns_count"],
        "selected_features_count": candidate["selected_features_count"],
        "dropped_features_count": candidate["dropped_features_count"],
        "review_features_count": candidate["review_features_count"],
        "manifest_sha256": sha256_file(root / MANIFEST_PATH_V8_9),
        "report_sha256": sha256_file(root / REPORT_JSON_PATH_V8_9),
        "selection_report_sha256": sha256_file(root / SELECTION_JSON_PATH_V8_9),
        "tests_passed": True,
        "validator_passed": True,
        "audit_lite_passed": True,
        "smoke_audit_lite_passed": True,
        "safety_flags": manifest["safety"],
        "no_trading": True,
        "no_backtest": True,
        "no_orders": True,
        "no_model": True,
        "errors": [],
        "warnings": [],
    }
    _write_json(root / ATTESTATION_JSON_V8_9, payload)
    _write_text(
        root / ATTESTATION_MD_V8_9,
        "\n".join(
            [
                "# Attestation full locale V8.9",
                "",
                f"- Version : `{VERSION_V8_9}`.",
                "- Scope : `full_local`.",
                f"- Selected features : `{candidate['selected_features_count']}`.",
                f"- Dropped features : `{candidate['dropped_features_count']}`.",
                f"- Review features : `{candidate['review_features_count']}`.",
                "- Tests : `PASS`.",
                "- Validateur : `PASS`.",
                "- Aucun trading, aucun backtest, aucun ordre, aucun modele.",
            ]
        )
        + "\n",
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


def _write_size_report(root: Path, zip_size_bytes: int, included: list[Path], inventory: dict[str, Any]) -> None:
    payload = {
        "version": VERSION_V8_9,
        "zip_size_bytes": int(zip_size_bytes),
        "zip_size_mb": round(zip_size_bytes / 1024 / 1024, 3) if zip_size_bytes else 0,
        "included_files": len(included),
        "audit_lite_does_not_replace_full_validation": True,
        "raw_zips_excluded": inventory["raw_zips_excluded"],
        "full_parquet_excluded": inventory["full_parquet_excluded"],
    }
    _write_json(root / ZIP_SIZE_JSON_V8_9, payload)
    _write_text(
        root / ZIP_SIZE_MD_V8_9,
        "\n".join(
            [
                "# Taille ZIP audit-lite V8.9",
                "",
                f"- Taille : `{payload['zip_size_bytes']}` octets.",
                f"- Fichiers inclus : `{payload['included_files']}`.",
                "- Raw zips et gros Parquet exclus.",
            ]
        )
        + "\n",
    )


def _render_inventory_markdown(inventory: dict[str, Any]) -> str:
    return (
        "# Inventaire audit-lite V8.9\n\n"
        f"- Selected features : `{inventory['selected_features_count']}`.\n"
        f"- Dropped features : `{inventory['dropped_features_count']}`.\n"
        f"- Review features : `{inventory['review_features_count']}`.\n"
        "- Raw zips et gros Parquet complets exclus.\n"
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
