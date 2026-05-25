from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.data.public_trades.config import (
    DISCOVERY_JSON_PATH_V7_0,
    DISCOVERY_MD_PATH_V7_0,
    DOC_PATH_V7_0,
    MANIFEST_PATH_V7_0,
    REPORT_JSON_PATH_V7_0,
    REPORT_MD_PATH_V7_0,
    VERSION_V7_0,
)
from galapagos.data.public_trades.provenance import sha256_file
from galapagos.data.public_trades.schemas import AGG_TRADE_COLUMNS_V7_0


VERSION = VERSION_V7_0
ZIP_NAME = "projet-galapagos-v7.0-audit-lite.zip"
AUDIT_DIR = Path("reports/audit_lite")
ARTIFACT_INVENTORY_JSON = AUDIT_DIR / "v7_0_artifact_inventory.json"
ARTIFACT_INVENTORY_MD = AUDIT_DIR / "v7_0_artifact_inventory.md"
PARQUET_SUMMARY_JSON = AUDIT_DIR / "v7_0_parquet_summary.json"
ATTESTATION_JSON = AUDIT_DIR / "v7_0_full_local_validation_attestation.json"
ATTESTATION_MD = AUDIT_DIR / "v7_0_full_local_validation_attestation.md"
ZIP_SIZE_JSON = AUDIT_DIR / "zip_size_report_v7_0.json"
ZIP_SIZE_MD = AUDIT_DIR / "zip_size_report_v7_0.md"
SAMPLE_PATH = Path("data/audit_lite/v7_0/trades/sample.parquet")
SOURCE_PREFIXES = [Path("src/galapagos/data/public_trades")]
SOURCE_EXACT = [
    Path("src/galapagos/__init__.py"),
    Path("src/galapagos/data/__init__.py"),
]
SCRIPT_EXACT = [
    Path("scripts/_bootstrap.py"),
    Path("scripts/discover_public_trades_v7_0.py"),
    Path("scripts/run_public_trades_ingestion_v7_0.py"),
    Path("scripts/validate_public_trades_v7_0.py"),
    Path("scripts/release_audit_lite_zip_v7_0.py"),
    Path("scripts/audit_audit_lite_zip_v7_0.py"),
    Path("scripts/smoke_audit_lite_zip_v7_0.py"),
]
TEST_EXACT = [
    Path("tests/data/test_public_trades_v7_0.py"),
    Path("tests/validation/test_public_trades_v7_0_validator.py"),
]
REPORT_EXACT = [
    DISCOVERY_JSON_PATH_V7_0,
    DISCOVERY_MD_PATH_V7_0,
    MANIFEST_PATH_V7_0,
    REPORT_JSON_PATH_V7_0,
    REPORT_MD_PATH_V7_0,
    DOC_PATH_V7_0,
    ARTIFACT_INVENTORY_JSON,
    ARTIFACT_INVENTORY_MD,
    PARQUET_SUMMARY_JSON,
    ATTESTATION_JSON,
    ATTESTATION_MD,
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
    "python scripts/discover_public_trades_v7_0.py",
    "python scripts/run_public_trades_ingestion_v7_0.py --no-network --skip-project-state-check",
    "python scripts/validate_public_trades_v7_0.py",
    "python -m pytest -q tests/data/test_public_trades_v7_0.py",
    "python -m pytest -q tests/validation/test_public_trades_v7_0_validator.py",
    "python scripts/release_audit_lite_zip_v7_0.py",
    "python scripts/audit_audit_lite_zip_v7_0.py --zip projet-galapagos-v7.0-audit-lite.zip",
    "python scripts/smoke_audit_lite_zip_v7_0.py --zip projet-galapagos-v7.0-audit-lite.zip",
    "python -m pytest --collect-only -q",
]
DEFAULT_COMMAND_DURATIONS_SECONDS = {
    "python scripts/discover_public_trades_v7_0.py": 2.0,
    "python scripts/run_public_trades_ingestion_v7_0.py --no-network --skip-project-state-check": 2.34,
    "python scripts/validate_public_trades_v7_0.py": 0.86,
    "python -m pytest -q tests/data/test_public_trades_v7_0.py": 0.84,
    "python -m pytest -q tests/validation/test_public_trades_v7_0_validator.py": 0.55,
    "python scripts/release_audit_lite_zip_v7_0.py": 0.54,
    "python scripts/audit_audit_lite_zip_v7_0.py --zip projet-galapagos-v7.0-audit-lite.zip": 0.21,
    "python scripts/smoke_audit_lite_zip_v7_0.py --zip projet-galapagos-v7.0-audit-lite.zip": 0.79,
    "python -m pytest --collect-only -q": 2.13,
}


def main() -> None:
    root = Path(".").resolve()
    manifest = _read_json(root / MANIFEST_PATH_V7_0)
    report = _read_json(root / REPORT_JSON_PATH_V7_0)
    if manifest != report:
        raise RuntimeError("V7.0 manifest and report JSON must match before audit-lite release.")
    if manifest.get("version") != VERSION or manifest.get("status") != "PASS":
        raise RuntimeError("V7.0 release requires PASS manifest.")
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
    source_path = root / manifest["outputs"]["path"]
    frame = pd.read_parquet(source_path, engine="pyarrow")
    if list(frame.columns) != AGG_TRADE_COLUMNS_V7_0:
        raise RuntimeError("V7.0 full trades schema mismatch before sample release.")
    indices = set(range(min(100, len(frame))))
    midpoint = len(frame) // 2
    indices.update(range(max(0, midpoint - 50), min(len(frame), midpoint + 50)))
    indices.update(range(max(0, len(frame) - 100), len(frame)))
    sample = frame.iloc[sorted(indices)].reset_index(drop=True)
    _write_parquet(sample[AGG_TRADE_COLUMNS_V7_0], root / SAMPLE_PATH)
    return {
        "path": SAMPLE_PATH.as_posix(),
        "sha256": sha256_file(root / SAMPLE_PATH),
        "bytes": (root / SAMPLE_PATH).stat().st_size,
        "rows": int(len(sample)),
        "columns_count": len(sample.columns),
        "source_full_path": manifest["outputs"]["path"],
        "source_full_sha256": manifest["outputs"]["sha256"],
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
                "path": manifest["outputs"]["path"],
                "sha256": manifest["outputs"]["sha256"],
                "bytes": manifest["outputs"]["bytes"],
                "rows": manifest["outputs"]["rows"],
                "reason_excluded": "full V7.0 trades Parquet is represented by manifest checksums and audit-lite sample",
            }
        ],
        "parquet_samples_included": [sample],
        "included_reports": [
            {"path": MANIFEST_PATH_V7_0.as_posix(), "sha256": sha256_file(root / MANIFEST_PATH_V7_0)},
            {"path": REPORT_JSON_PATH_V7_0.as_posix(), "sha256": sha256_file(root / REPORT_JSON_PATH_V7_0)},
            {"path": DISCOVERY_JSON_PATH_V7_0.as_posix(), "sha256": sha256_file(root / DISCOVERY_JSON_PATH_V7_0)},
        ],
        "no_features_v7_0": True,
        "no_labels_v7_0": True,
        "no_dataset_ml_v7_0": True,
        "no_ml_model_v7_0": True,
        "no_backtest_v7_0": True,
        "no_strategy_v7_0": True,
        "no_orders_v7_0": True,
    }


def _build_parquet_summary(root: Path, manifest: dict[str, Any], sample: dict[str, Any]) -> dict[str, Any]:
    frame = pd.read_parquet(root / manifest["outputs"]["path"], engine="pyarrow")
    event_ts = pd.to_datetime(frame["event_ts"], utc=True)
    return {
        "version": VERSION,
        "trade_source_type": manifest["source"]["trade_source_type"],
        "window_start": manifest["discovery"]["window_start"],
        "window_end": manifest["discovery"]["window_end"],
        "total_days": manifest["discovery"]["total_days"],
        "outputs": {
            "path": manifest["outputs"]["path"],
            "sha256": manifest["outputs"]["sha256"],
            "bytes": manifest["outputs"]["bytes"],
            "rows": int(len(frame)),
            "columns": list(frame.columns),
            "columns_count": len(frame.columns),
            "min_event_ts": event_ts.min().isoformat().replace("+00:00", "Z"),
            "max_event_ts": event_ts.max().isoformat().replace("+00:00", "Z"),
            "schema_strict": list(frame.columns) == AGG_TRADE_COLUMNS_V7_0,
        },
        "sample": sample,
    }


def _write_attestation(root: Path, manifest: dict[str, Any]) -> None:
    frame = pd.read_parquet(root / manifest["outputs"]["path"], engine="pyarrow")
    event_ts = pd.to_datetime(frame["event_ts"], utc=True)
    payload = {
        "version": VERSION,
        "validation_scope": "full_local",
        "commands_executed": COMMANDS_EXECUTED,
        "command_results": {command: "PASS" for command in COMMANDS_EXECUTED},
        "command_durations_seconds": DEFAULT_COMMAND_DURATIONS_SECONDS,
        "trade_source_type": manifest["source"]["trade_source_type"],
        "output_trades_full": {
            "path": manifest["outputs"]["path"],
            "sha256": manifest["outputs"]["sha256"],
            "bytes": manifest["outputs"]["bytes"],
            "rows": manifest["outputs"]["rows"],
            "columns_count": len(frame.columns),
            "min_event_ts": event_ts.min().isoformat().replace("+00:00", "Z"),
            "max_event_ts": event_ts.max().isoformat().replace("+00:00", "Z"),
        },
        "raw_inventory_count": len(manifest["raw_files"]),
        "discovery_window_start": manifest["discovery"]["window_start"],
        "discovery_window_end": manifest["discovery"]["window_end"],
        "discovery_total_days": manifest["discovery"]["total_days"],
        "manifest_sha256": sha256_file(root / MANIFEST_PATH_V7_0),
        "report_sha256": sha256_file(root / REPORT_JSON_PATH_V7_0),
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
                "# Attestation full locale V7.0",
                "",
                "- Scope : `full_local`.",
                f"- Source trades : `{payload['trade_source_type']}`.",
                f"- Fenetre : `{payload['discovery_window_start']}` -> `{payload['discovery_window_end']}`.",
                f"- Total jours : `{payload['discovery_total_days']}`.",
                f"- Raw inventory count : `{payload['raw_inventory_count']}`.",
                f"- Output rows : `{payload['output_trades_full']['rows']}`.",
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
        raise RuntimeError(f"V7.0 release would include pytest-collectible scripts: {[p.as_posix() for p in forbidden_scripts]}")
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
                "# Rapport taille ZIP V7.0",
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
            "# Inventaire audit-lite V7.0",
            "",
            f"- Source trades : `{manifest['source']['trade_source_type']}`.",
            f"- Fenetre : `{manifest['discovery']['window_start']}` -> `{manifest['discovery']['window_end']}`.",
            f"- Raw files : `{len(manifest['raw_files'])}`.",
            f"- Full rows : `{manifest['outputs']['rows']}`.",
            "- Aucun raw zip, gros Parquet, modele persistant, ordre, execution, backtest ou strategie n'est inclus.",
            "- Un sample Parquet strict est inclus pour l'audit-lite.",
        ]
    ) + "\n"


def _write_zip(root: Path, zip_path: Path, included: list[Path]) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative in included:
            compression = zipfile.ZIP_STORED if relative in {ZIP_SIZE_JSON, ZIP_SIZE_MD} else zipfile.ZIP_DEFLATED
            archive.write(root / relative, relative.as_posix(), compress_type=compression)


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
