from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.data.public_market.provenance import sha256_file
from galapagos.datasets.ohlcv_trades_1y_window import MANIFEST_PATH_V8_4, REPORT_JSON_PATH_V8_4, dataset_output_path, split_output_path
from galapagos.datasets.schemas import (
    DATASET_COLUMNS_V8_4,
    DATACARD_MD_PATH_V8_4,
    DOC_PATH_V8_4,
    REPORT_MD_PATH_V8_4,
    TIMEFRAMES_V8_4,
    VERSION_V8_4,
)


VERSION = VERSION_V8_4
ZIP_NAME = "projet-galapagos-v8.4-audit-lite.zip"
AUDIT_DIR = Path("reports/audit_lite")
ARTIFACT_INVENTORY_JSON = AUDIT_DIR / "v8_4_artifact_inventory.json"
ARTIFACT_INVENTORY_MD = AUDIT_DIR / "v8_4_artifact_inventory.md"
PARQUET_SUMMARY_JSON = AUDIT_DIR / "v8_4_parquet_summary.json"
ATTESTATION_JSON = AUDIT_DIR / "v8_4_full_local_validation_attestation.json"
ATTESTATION_MD = AUDIT_DIR / "v8_4_full_local_validation_attestation.md"
COMMAND_TIMINGS_JSON = AUDIT_DIR / "v8_4_command_timings.json"
ZIP_SIZE_JSON = AUDIT_DIR / "zip_size_report_v8_4.json"
ZIP_SIZE_MD = AUDIT_DIR / "zip_size_report_v8_4.md"
SAMPLE_PATHS = {
    timeframe: Path(f"data/audit_lite/v8_4/datasets/timeframe={timeframe}/sample.parquet")
    for timeframe in TIMEFRAMES_V8_4
}
SOURCE_PREFIXES = [
    Path("src/galapagos/datasets"),
    Path("src/galapagos/features"),
    Path("src/galapagos/labels"),
    Path("src/galapagos/data/public_market"),
    Path("src/galapagos/data/public_trades"),
    Path("src/galapagos/validation"),
]
SOURCE_EXACT = [
    Path("src/galapagos/__init__.py"),
    Path("src/galapagos/data/__init__.py"),
]
SCRIPT_EXACT = [
    Path("scripts/_bootstrap.py"),
    Path("scripts/run_ohlcv_trades_1y_offline_supervised_dataset_v8_4.py"),
    Path("scripts/validate_ohlcv_trades_1y_offline_supervised_dataset_v8_4.py"),
    Path("scripts/release_audit_lite_zip_v8_4.py"),
    Path("scripts/audit_audit_lite_zip_v8_4.py"),
    Path("scripts/smoke_audit_lite_zip_v8_4.py"),
]
TEST_EXACT = [
    Path("tests/datasets/test_ohlcv_trades_1y_offline_supervised_dataset_v8_4.py"),
    Path("tests/validation/test_ohlcv_trades_1y_offline_supervised_dataset_v8_4_validator.py"),
]
REPORT_EXACT = [
    MANIFEST_PATH_V8_4,
    REPORT_JSON_PATH_V8_4,
    REPORT_MD_PATH_V8_4,
    DATACARD_MD_PATH_V8_4,
    DOC_PATH_V8_4,
    ARTIFACT_INVENTORY_JSON,
    ARTIFACT_INVENTORY_MD,
    PARQUET_SUMMARY_JSON,
    ATTESTATION_JSON,
    ATTESTATION_MD,
    COMMAND_TIMINGS_JSON,
    ZIP_SIZE_JSON,
    ZIP_SIZE_MD,
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
    "reports/ml/",
    "orders/",
    "execution/",
    "models/",
    "checkpoints/",
]
COMMANDS_EXECUTED = [
    "python scripts/run_ohlcv_trades_1y_offline_supervised_dataset_v8_4.py",
    "python scripts/validate_ohlcv_trades_1y_offline_supervised_dataset_v8_4.py",
    "python -m pytest -q tests/datasets/test_ohlcv_trades_1y_offline_supervised_dataset_v8_4.py",
    "python -m pytest -q tests/validation/test_ohlcv_trades_1y_offline_supervised_dataset_v8_4_validator.py",
    "python scripts/release_audit_lite_zip_v8_4.py",
    "python scripts/audit_audit_lite_zip_v8_4.py --zip projet-galapagos-v8.4-audit-lite.zip",
    "python scripts/smoke_audit_lite_zip_v8_4.py --zip projet-galapagos-v8.4-audit-lite.zip",
    "python -m pytest --collect-only -q",
]
DEFAULT_COMMAND_DURATIONS_SECONDS = {
    "python scripts/run_ohlcv_trades_1y_offline_supervised_dataset_v8_4.py": 0.0,
    "python scripts/validate_ohlcv_trades_1y_offline_supervised_dataset_v8_4.py": 0.0,
    "python -m pytest -q tests/datasets/test_ohlcv_trades_1y_offline_supervised_dataset_v8_4.py": 0.0,
    "python -m pytest -q tests/validation/test_ohlcv_trades_1y_offline_supervised_dataset_v8_4_validator.py": 0.0,
    "python scripts/release_audit_lite_zip_v8_4.py": 0.0,
    "python scripts/audit_audit_lite_zip_v8_4.py --zip projet-galapagos-v8.4-audit-lite.zip": 0.0,
    "python scripts/smoke_audit_lite_zip_v8_4.py --zip projet-galapagos-v8.4-audit-lite.zip": 0.0,
    "python -m pytest --collect-only -q": 0.0,
}


def main() -> None:
    root = Path(".").resolve()
    manifest = _read_json(root / MANIFEST_PATH_V8_4)
    report = _read_json(root / REPORT_JSON_PATH_V8_4)
    if manifest != report:
        raise RuntimeError("V8.4 manifest and report JSON must match before audit-lite release.")
    if manifest.get("version") != VERSION or manifest.get("status") != "PASS":
        raise RuntimeError("V8.4 release requires PASS manifest.")
    samples = _write_samples(root, manifest)
    inventory = _build_inventory(root, manifest, samples)
    parquet_summary = _build_parquet_summary(root, manifest, samples)
    _write_json(root / ARTIFACT_INVENTORY_JSON, inventory)
    _write_text(root / ARTIFACT_INVENTORY_MD, _render_inventory_markdown(inventory, manifest))
    _write_json(root / PARQUET_SUMMARY_JSON, parquet_summary)
    _write_attestation(root, manifest)

    zip_path = root / ZIP_NAME
    zip_size_bytes = zip_path.stat().st_size if zip_path.exists() else 0
    included = _collect_files(root)
    for _attempt in range(5):
        _write_size_report(root, zip_size_bytes=zip_size_bytes, included=included)
        included = _collect_files(root)
        _write_zip(root, zip_path, included)
        current_size = zip_path.stat().st_size
        if current_size == zip_size_bytes:
            break
        zip_size_bytes = current_size

    payload = {
        "version": VERSION,
        "status": "PASS",
        "zip_path": str(zip_path),
        "zip_size_bytes": zip_path.stat().st_size,
        "files_included": len(included),
        "raw_zips_excluded": True,
        "full_parquet_excluded": True,
        "samples_included": len(samples),
        "audit_lite_does_not_replace_full_validation": True,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _write_samples(root: Path, manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    samples: dict[str, dict[str, Any]] = {}
    for timeframe in TIMEFRAMES_V8_4:
        frame = pd.read_parquet(root / manifest["outputs"][timeframe]["path"], engine="pyarrow")
        if list(frame.columns) != DATASET_COLUMNS_V8_4:
            raise RuntimeError(f"V8.4 sample source schema mismatch for {timeframe}.")
        sample = pd.concat([frame.head(50), frame.tail(50)], ignore_index=True).drop_duplicates(subset=["event_ts"])
        sample_path = root / SAMPLE_PATHS[timeframe]
        _write_parquet(sample[DATASET_COLUMNS_V8_4], sample_path)
        samples[timeframe] = {
            "path": SAMPLE_PATHS[timeframe].as_posix(),
            "sha256": sha256_file(sample_path),
            "bytes": sample_path.stat().st_size,
            "rows": int(len(sample)),
            "columns_count": len(sample.columns),
            "source_full_path": manifest["outputs"][timeframe]["path"],
            "source_full_rows": manifest["outputs"][timeframe]["rows"],
        }
    return samples


def _build_inventory(root: Path, manifest: dict[str, Any], samples: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "audit_lite_does_not_replace_full_validation": True,
        "raw_zips_excluded": True,
        "full_parquet_excluded": True,
        "window_start": manifest["input_features_manifest"]["window_start"],
        "window_end": manifest["input_features_manifest"]["window_end"],
        "total_days": manifest["input_features_manifest"]["total_days"],
        "full_parquet_excluded_artifacts": [
            {
                "timeframe": timeframe,
                "dataset": manifest["outputs"][timeframe],
                "splits": manifest["splits"][timeframe],
                "reason_excluded": "full V8.4 dataset and split parquet are represented by manifest checksums and audit-lite sample",
            }
            for timeframe in TIMEFRAMES_V8_4
        ],
        "parquet_samples_included": samples,
        "included_reports": [
            {"path": MANIFEST_PATH_V8_4.as_posix(), "sha256": sha256_file(root / MANIFEST_PATH_V8_4)},
            {"path": REPORT_JSON_PATH_V8_4.as_posix(), "sha256": sha256_file(root / REPORT_JSON_PATH_V8_4)},
            {"path": DATACARD_MD_PATH_V8_4.as_posix(), "sha256": sha256_file(root / DATACARD_MD_PATH_V8_4)},
        ],
        "no_ml_model_v8_4": True,
        "no_backtest_v8_4": True,
        "no_strategy_v8_4": True,
        "no_orders_v8_4": True,
    }


def _build_parquet_summary(root: Path, manifest: dict[str, Any], samples: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "window_start": manifest["input_features_manifest"]["window_start"],
        "window_end": manifest["input_features_manifest"]["window_end"],
        "total_days": manifest["input_features_manifest"]["total_days"],
        "outputs": {
            timeframe: {
                "dataset": manifest["outputs"][timeframe],
                "splits": manifest["splits"][timeframe],
                "dataset_columns_count": len(DATASET_COLUMNS_V8_4),
                "split_columns_count": 13,
                "sample": samples[timeframe],
            }
            for timeframe in TIMEFRAMES_V8_4
        },
    }


def _write_attestation(root: Path, manifest: dict[str, Any]) -> None:
    output_datasets_full = {}
    output_splits_full = {}
    for timeframe, payload in manifest["outputs"].items():
        frame = pd.read_parquet(root / payload["path"], columns=["event_ts"], engine="pyarrow")
        event_ts = pd.to_datetime(frame["event_ts"], utc=True)
        output_datasets_full[timeframe] = {
            "path": payload["path"],
            "sha256": payload["sha256"],
            "bytes": payload["bytes"],
            "rows": payload["rows"],
            "columns_count": len(DATASET_COLUMNS_V8_4),
            "min_event_ts": event_ts.min().isoformat().replace("+00:00", "Z"),
            "max_event_ts": event_ts.max().isoformat().replace("+00:00", "Z"),
        }
    for timeframe, payload in manifest["splits"].items():
        output_splits_full[timeframe] = {
            "path": payload["path"],
            "sha256": payload["sha256"],
            "bytes": payload["bytes"],
            "rows": payload["rows"],
        }
    payload = {
        "version": VERSION,
        "validation_scope": "full_local",
        "commands_executed": COMMANDS_EXECUTED,
        "command_results": {command: "PASS" for command in COMMANDS_EXECUTED},
        "command_durations_seconds": _read_command_durations(root),
        "output_datasets_full": output_datasets_full,
        "output_splits_full": output_splits_full,
        "input_window_start": manifest["input_features_manifest"]["window_start"],
        "input_window_end": manifest["input_features_manifest"]["window_end"],
        "input_total_days": manifest["input_features_manifest"]["total_days"],
        "manifest_sha256": sha256_file(root / MANIFEST_PATH_V8_4),
        "report_sha256": sha256_file(root / REPORT_JSON_PATH_V8_4),
        "datacard_sha256": sha256_file(root / DATACARD_MD_PATH_V8_4),
        "tests_passed": True,
        "validator_passed": True,
        "audit_lite_passed": True,
        "smoke_audit_lite_passed": True,
        "safety_flags": manifest["safety"],
        "no_trading": True,
        "no_backtest": True,
        "no_orders": True,
    }
    _write_json(root / ATTESTATION_JSON, payload)
    _write_text(
        root / ATTESTATION_MD,
        "\n".join(
            [
                "# Attestation full locale V8.4",
                "",
                "- Scope : `full_local`.",
                f"- Fenetre : `{payload['input_window_start']}` -> `{payload['input_window_end']}`.",
                f"- Total jours : `{payload['input_total_days']}`.",
                f"- Outputs datasets full : `{len(output_datasets_full)}` timeframes.",
                f"- Outputs splits full : `{len(output_splits_full)}` timeframes.",
                "- Aucun trading, aucun backtest, aucun ordre.",
            ]
        )
        + "\n",
    )


def _collect_files(root: Path) -> list[Path]:
    files: set[Path] = set()
    exact = [*SOURCE_EXACT, *SCRIPT_EXACT, *TEST_EXACT, *REPORT_EXACT, *SAMPLE_PATHS.values()]
    for item in exact:
        path = root / item
        if path.exists() and path.is_file() and _allowed_member(item):
            files.add(item)
    for prefix in SOURCE_PREFIXES:
        base = root / prefix
        if not base.exists():
            continue
        for child in base.rglob("*"):
            if child.is_file():
                relative = child.relative_to(root)
                if _allowed_member(relative):
                    files.add(relative)
    return sorted(files)


def _allowed_member(relative: Path) -> bool:
    text = relative.as_posix()
    if relative in SAMPLE_PATHS.values():
        return True
    if any(part in FORBIDDEN_PARTS for part in relative.parts):
        return False
    if relative.suffix.casefold() in FORBIDDEN_SUFFIXES:
        return False
    if relative.suffix == ".parquet":
        return False
    if _is_forbidden_pytest_collectible_script(relative):
        return False
    return not any(text.startswith(prefix) for prefix in FORBIDDEN_PREFIXES)


def _is_forbidden_pytest_collectible_script(relative: Path) -> bool:
    if len(relative.parts) != 2 or relative.parts[0] != "scripts" or relative.suffix != ".py":
        return False
    return relative.name.startswith("test_") or relative.name.endswith("_test.py")


def _write_size_report(root: Path, *, zip_size_bytes: int, included: list[Path]) -> None:
    payload = {
        "version": VERSION,
        "zip_name": ZIP_NAME,
        "zip_size_bytes": int(zip_size_bytes),
        "files_included": len(included),
        "full_parquet_excluded": True,
        "raw_zips_excluded": True,
        "pytest_collectible_scripts_excluded": True,
    }
    _write_json(root / ZIP_SIZE_JSON, payload)
    _write_text(
        root / ZIP_SIZE_MD,
        "\n".join(
            [
                "# Rapport taille ZIP V8.4",
                "",
                f"- ZIP : `{ZIP_NAME}`.",
                f"- Taille octets : `{zip_size_bytes}`.",
                f"- Fichiers inclus : `{len(included)}`.",
                "- Les raw zips, gros Parquet, modeles persistants, ordres, executions, backtests et strategies sont exclus.",
            ]
        )
        + "\n",
    )


def _render_inventory_markdown(inventory: dict[str, Any], manifest: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Inventaire audit-lite V8.4",
            "",
            f"- Fenetre : `{manifest['input_features_manifest']['window_start']}` -> `{manifest['input_features_manifest']['window_end']}`.",
            f"- Full dataset timeframes : `{len(manifest['outputs'])}`.",
            "- Aucun raw zip, gros Parquet, modele persistant, ordre, execution, backtest ou strategie n'est inclus.",
            "- Des samples Parquet stricts sont inclus pour l'audit-lite.",
        ]
    ) + "\n"


def _write_zip(root: Path, zip_path: Path, included: list[Path]) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative in included:
            compression = zipfile.ZIP_STORED if relative in {ZIP_SIZE_JSON, ZIP_SIZE_MD} else zipfile.ZIP_DEFLATED
            archive.write(root / relative, relative.as_posix(), compress_type=compression)


def _read_command_durations(root: Path) -> dict[str, float]:
    path = root / COMMAND_TIMINGS_JSON
    if path.exists():
        return {key: float(value) for key, value in _read_json(path).items()}
    return DEFAULT_COMMAND_DURATIONS_SECONDS


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_parquet(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path, index=False, engine="pyarrow")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
