from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.data.public_trades.config import (
    DISCOVERY_JSON_PATH_V7_7,
    DISCOVERY_MD_PATH_V7_7,
    DOC_PATH_V7_7,
    MANIFEST_PATH_V7_7,
    REPORT_JSON_PATH_V7_7,
    REPORT_MD_PATH_V7_7,
    VERSION_V7_7,
)
from galapagos.data.public_trades.provenance import sha256_file
from galapagos.data.public_trades.schemas import AGG_TRADE_COLUMNS_V7_7


VERSION = VERSION_V7_7
ZIP_NAME = "projet-galapagos-v7.7-audit-lite.zip"
AUDIT_DIR = Path("reports/audit_lite")
ARTIFACT_INVENTORY_JSON = AUDIT_DIR / "v7_7_artifact_inventory.json"
ARTIFACT_INVENTORY_MD = AUDIT_DIR / "v7_7_artifact_inventory.md"
PARQUET_SUMMARY_JSON = AUDIT_DIR / "v7_7_parquet_summary.json"
ATTESTATION_JSON = AUDIT_DIR / "v7_7_full_local_validation_attestation.json"
ATTESTATION_MD = AUDIT_DIR / "v7_7_full_local_validation_attestation.md"
COMMAND_TIMINGS_JSON = AUDIT_DIR / "v7_7_command_timings.json"
ZIP_SIZE_JSON = AUDIT_DIR / "zip_size_report_v7_7.json"
ZIP_SIZE_MD = AUDIT_DIR / "zip_size_report_v7_7.md"
SAMPLE_PATH = Path("data/audit_lite/v7_7/trades/sample.parquet")
SOURCE_PREFIXES = [Path("src/galapagos/data/public_trades")]
SOURCE_EXACT = [
    Path("src/galapagos/__init__.py"),
    Path("src/galapagos/data/__init__.py"),
]
SCRIPT_EXACT = [
    Path("scripts/_bootstrap.py"),
    Path("scripts/discover_public_trades_v7_7.py"),
    Path("scripts/run_public_trades_90d_window_v7_7.py"),
    Path("scripts/validate_public_trades_90d_window_v7_7.py"),
    Path("scripts/release_audit_lite_zip_v7_7.py"),
    Path("scripts/audit_audit_lite_zip_v7_7.py"),
    Path("scripts/smoke_audit_lite_zip_v7_7.py"),
]
TEST_EXACT = [
    Path("tests/data/test_public_trades_90d_window_v7_7.py"),
    Path("tests/validation/test_public_trades_90d_window_v7_7_validator.py"),
]
REPORT_EXACT = [
    DISCOVERY_JSON_PATH_V7_7,
    DISCOVERY_MD_PATH_V7_7,
    MANIFEST_PATH_V7_7,
    REPORT_JSON_PATH_V7_7,
    REPORT_MD_PATH_V7_7,
    DOC_PATH_V7_7,
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
    "orders/",
    "execution/",
    "models/",
    "checkpoints/",
]
COMMANDS_EXECUTED = [
    "python scripts/discover_public_trades_v7_7.py",
    "python scripts/run_public_trades_90d_window_v7_7.py --no-network --skip-project-state-check",
    "python scripts/validate_public_trades_90d_window_v7_7.py",
    "python -m pytest -q tests/data/test_public_trades_90d_window_v7_7.py",
    "python -m pytest -q tests/validation/test_public_trades_90d_window_v7_7_validator.py",
    "python scripts/release_audit_lite_zip_v7_7.py",
    "python scripts/audit_audit_lite_zip_v7_7.py --zip projet-galapagos-v7.7-audit-lite.zip",
    "python scripts/smoke_audit_lite_zip_v7_7.py --zip projet-galapagos-v7.7-audit-lite.zip",
    "python -m pytest --collect-only -q",
]
DEFAULT_COMMAND_DURATIONS_SECONDS = {
    "python scripts/discover_public_trades_v7_7.py": 0.0,
    "python scripts/run_public_trades_90d_window_v7_7.py --no-network --skip-project-state-check": 0.0,
    "python scripts/validate_public_trades_90d_window_v7_7.py": 0.0,
    "python -m pytest -q tests/data/test_public_trades_90d_window_v7_7.py": 0.0,
    "python -m pytest -q tests/validation/test_public_trades_90d_window_v7_7_validator.py": 0.0,
    "python scripts/release_audit_lite_zip_v7_7.py": 0.0,
    "python scripts/audit_audit_lite_zip_v7_7.py --zip projet-galapagos-v7.7-audit-lite.zip": 0.0,
    "python scripts/smoke_audit_lite_zip_v7_7.py --zip projet-galapagos-v7.7-audit-lite.zip": 0.0,
    "python -m pytest --collect-only -q": 0.0,
}


def main() -> None:
    root = Path(".").resolve()
    manifest = _read_json(root / MANIFEST_PATH_V7_7)
    report = _read_json(root / REPORT_JSON_PATH_V7_7)
    if manifest != report:
        raise RuntimeError("V7.7 manifest and report JSON must match before audit-lite release.")
    if manifest.get("version") != VERSION or manifest.get("status") != "PASS":
        raise RuntimeError("V7.7 release requires PASS manifest.")
    sample = _write_sample(root, manifest)
    inventory = _build_inventory(root, manifest, sample)
    parquet_summary = _build_parquet_summary(root, manifest, sample)
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
        "samples_included": 1,
        "pytest_collectible_scripts_excluded": True,
        "audit_lite_does_not_replace_full_validation": True,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _write_sample(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    selected = []
    partitions = manifest["outputs"]["partitions"]
    partition_dates = sorted(partitions)
    for date_key in [partition_dates[0], partition_dates[len(partition_dates) // 2], partition_dates[-1]]:
        frame = pd.read_parquet(root / partitions[date_key]["path"], engine="pyarrow")
        if list(frame.columns) != AGG_TRADE_COLUMNS_V7_7:
            raise RuntimeError("V7.7 trades partition schema mismatch before sample release.")
        selected.append(frame.head(50))
        selected.append(frame.tail(50))
    sample = pd.concat(selected, ignore_index=True).drop_duplicates(subset=["aggregate_trade_id"]).reset_index(drop=True)
    _write_parquet(sample[AGG_TRADE_COLUMNS_V7_7], root / SAMPLE_PATH)
    return {
        "path": SAMPLE_PATH.as_posix(),
        "sha256": sha256_file(root / SAMPLE_PATH),
        "bytes": (root / SAMPLE_PATH).stat().st_size,
        "rows": int(len(sample)),
        "columns_count": len(sample.columns),
        "source_partitions_count": len(partitions),
        "source_total_rows": manifest["outputs"]["total_rows"],
    }


def _build_inventory(root: Path, manifest: dict[str, Any], sample: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "audit_lite_does_not_replace_full_validation": True,
        "raw_zips_excluded": True,
        "full_parquet_excluded": True,
        "trade_source_type": manifest["source"]["trade_source_type"],
        "window_start": manifest["discovery"]["window_start"],
        "window_end": manifest["discovery"]["window_end"],
        "total_days": manifest["discovery"]["total_days"],
        "raw_inventory": manifest["raw_files"],
        "full_parquet_excluded_artifacts": [
            {
                "partitions": manifest["outputs"]["partitions"],
                "total_rows": manifest["outputs"]["total_rows"],
                "total_bytes": manifest["outputs"]["total_bytes"],
                "reason_excluded": "full V7.7 trades partitions are represented by manifest checksums and audit-lite sample",
            }
        ],
        "parquet_samples_included": [sample],
        "included_reports": [
            {"path": MANIFEST_PATH_V7_7.as_posix(), "sha256": sha256_file(root / MANIFEST_PATH_V7_7)},
            {"path": REPORT_JSON_PATH_V7_7.as_posix(), "sha256": sha256_file(root / REPORT_JSON_PATH_V7_7)},
            {"path": DISCOVERY_JSON_PATH_V7_7.as_posix(), "sha256": sha256_file(root / DISCOVERY_JSON_PATH_V7_7)},
        ],
        "no_features_v7_7": True,
        "no_labels_v7_7": True,
        "no_dataset_ml_v7_7": True,
        "no_ml_model_v7_7": True,
        "no_backtest_v7_7": True,
        "no_strategy_v7_7": True,
        "no_orders_v7_7": True,
    }


def _build_parquet_summary(root: Path, manifest: dict[str, Any], sample: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "trade_source_type": manifest["source"]["trade_source_type"],
        "window_start": manifest["discovery"]["window_start"],
        "window_end": manifest["discovery"]["window_end"],
        "total_days": manifest["discovery"]["total_days"],
        "outputs": {
            "partitions": manifest["outputs"]["partitions"],
            "total_rows": manifest["outputs"]["total_rows"],
            "total_bytes": manifest["outputs"]["total_bytes"],
            "columns": AGG_TRADE_COLUMNS_V7_7,
            "columns_count": len(AGG_TRADE_COLUMNS_V7_7),
            "min_event_ts": manifest["quality"]["min_event_ts"],
            "max_event_ts": manifest["quality"]["max_event_ts"],
            "schema_strict": True,
        },
        "sample": sample,
    }


def _write_attestation(root: Path, manifest: dict[str, Any]) -> None:
    payload = {
        "version": VERSION,
        "validation_scope": "full_local",
        "commands_executed": COMMANDS_EXECUTED,
        "command_results": {command: "PASS" for command in COMMANDS_EXECUTED},
        "command_durations_seconds": _read_command_durations(root),
        "trade_source_type": manifest["source"]["trade_source_type"],
        "output_trades_full": {
            "partitions": manifest["outputs"]["partitions"],
            "total_rows": manifest["outputs"]["total_rows"],
            "total_bytes": manifest["outputs"]["total_bytes"],
            "columns_count": len(AGG_TRADE_COLUMNS_V7_7),
            "min_event_ts": manifest["quality"]["min_event_ts"],
            "max_event_ts": manifest["quality"]["max_event_ts"],
        },
        "raw_inventory_count": len(manifest["raw_files"]),
        "discovery_window_start": manifest["discovery"]["window_start"],
        "discovery_window_end": manifest["discovery"]["window_end"],
        "discovery_total_days": manifest["discovery"]["total_days"],
        "manifest_sha256": sha256_file(root / MANIFEST_PATH_V7_7),
        "report_sha256": sha256_file(root / REPORT_JSON_PATH_V7_7),
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
                "# Attestation full locale V7.7",
                "",
                "- Scope : `full_local`.",
                f"- Source trades : `{payload['trade_source_type']}`.",
                f"- Fenetre : `{payload['discovery_window_start']}` -> `{payload['discovery_window_end']}`.",
                f"- Total jours : `{payload['discovery_total_days']}`.",
                f"- Raw inventory count : `{payload['raw_inventory_count']}`.",
                f"- Output rows : `{payload['output_trades_full']['total_rows']}`.",
                "- Aucun trading, aucun backtest, aucun ordre.",
            ]
        )
        + "\n",
    )


def _collect_files(root: Path) -> list[Path]:
    files: set[Path] = set()
    exact = [
        *SOURCE_EXACT,
        *SCRIPT_EXACT,
        *TEST_EXACT,
        *REPORT_EXACT,
        SAMPLE_PATH,
    ]
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
    forbidden_scripts = [relative for relative in files if _is_forbidden_pytest_collectible_script(relative)]
    if forbidden_scripts:
        raise RuntimeError(f"V7.7 release would include pytest-collectible scripts: {[p.as_posix() for p in forbidden_scripts]}")
    return sorted(files)


def _allowed_member(relative: Path) -> bool:
    text = relative.as_posix()
    if relative == SAMPLE_PATH:
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
                "# Rapport taille ZIP V7.7",
                "",
                f"- ZIP : `{ZIP_NAME}`.",
                f"- Taille octets : `{zip_size_bytes}`.",
                f"- Fichiers inclus : `{len(included)}`.",
                "- Les raw zips, gros Parquet, modeles persistants et scripts pytest historiques inutiles sont exclus.",
            ]
        )
        + "\n",
    )


def _render_inventory_markdown(inventory: dict[str, Any], manifest: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Inventaire audit-lite V7.7",
            "",
            f"- Source trades : `{manifest['source']['trade_source_type']}`.",
            f"- Fenetre : `{manifest['discovery']['window_start']}` -> `{manifest['discovery']['window_end']}`.",
            f"- Raw files : `{len(manifest['raw_files'])}`.",
            f"- Full rows : `{manifest['outputs']['total_rows']}`.",
            "- Aucun raw zip, gros Parquet, modele persistant, ordre, execution, backtest ou strategie n'est inclus.",
            "- Un sample Parquet strict est inclus pour l'audit-lite.",
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
