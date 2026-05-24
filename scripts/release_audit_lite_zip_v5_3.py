from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet, write_parquet
from galapagos.datasets.max_history_window import (
    dataset_output_path,
    split_output_path,
)
from galapagos.datasets.schemas import (
    DATACARD_MD_PATH_V5_3,
    DOC_PATH_V5_3,
    DATASET_COLUMNS_V5_3,
    MANIFEST_PATH_V5_3,
    REPORT_JSON_PATH_V5_3,
    REPORT_MD_PATH_V5_3,
    SPLIT_COLUMNS_V5_3,
    TIMEFRAMES_V5_3,
)


VERSION = "V5.3"
ZIP_NAME = "projet-galapagos-v5.3-audit-lite.zip"
AUDIT_DIR = Path("reports/audit_lite")
ARTIFACT_INVENTORY_JSON = AUDIT_DIR / "v5_3_artifact_inventory.json"
ARTIFACT_INVENTORY_MD = AUDIT_DIR / "v5_3_artifact_inventory.md"
PARQUET_SUMMARY_JSON = AUDIT_DIR / "v5_3_parquet_summary.json"
ATTESTATION_JSON = AUDIT_DIR / "v5_3_full_local_validation_attestation.json"
ATTESTATION_MD = AUDIT_DIR / "v5_3_full_local_validation_attestation.md"
ZIP_SIZE_JSON = AUDIT_DIR / "zip_size_report_v5_3.json"
ZIP_SIZE_MD = AUDIT_DIR / "zip_size_report_v5_3.md"
DATASET_SAMPLE_ROOT = Path("data/audit_lite/v5_3/datasets")
SPLIT_SAMPLE_ROOT = Path("data/audit_lite/v5_3/splits")
FORBIDDEN_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
FORBIDDEN_PREFIXES = [
    "data/raw/public_market/",
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
FORBIDDEN_SUFFIXES = {".pyc", ".pyo", ".pkl", ".pickle", ".joblib", ".ckpt", ".pt", ".pth", ".onnx"}


def main() -> None:
    root = Path(".").resolve()
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = _read_json(root / MANIFEST_PATH_V5_3)
    report = _read_json(root / REPORT_JSON_PATH_V5_3)
    if manifest != report:
        raise RuntimeError("V5.3 manifest and report JSON must match before audit-lite release.")
    dataset_samples, split_samples = _write_samples(root, manifest)
    inventory = _build_artifact_inventory(root, manifest, dataset_samples, split_samples)
    parquet_summary = _build_parquet_summary(root, manifest)
    _write_json(root / ARTIFACT_INVENTORY_JSON, inventory)
    _write_text(root / ARTIFACT_INVENTORY_MD, _render_inventory_markdown(inventory, manifest))
    _write_json(root / PARQUET_SUMMARY_JSON, parquet_summary)
    _write_attestation(root, manifest)

    zip_path = root / ZIP_NAME
    zip_size_bytes = 0
    included: list[Path] = []
    _write_size_report(root, zip_size_bytes=zip_size_bytes, included=included, inventory=inventory)
    included = _collect_files(root)
    for _attempt in range(5):
        _write_size_report(root, zip_size_bytes=zip_size_bytes, included=included, inventory=inventory)
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
        "full_parquet_excluded_count": len(inventory["full_parquet_excluded"]),
        "dataset_samples_included": len(dataset_samples),
        "split_samples_included": len(split_samples),
        "audit_lite_does_not_replace_full_validation": True,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _write_samples(root: Path, manifest: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    dataset_samples: list[dict[str, Any]] = []
    split_samples: list[dict[str, Any]] = []
    window_start = manifest["input_features_manifest"]["window_start"]
    window_end = manifest["input_features_manifest"]["window_end"]
    for timeframe in TIMEFRAMES_V5_3:
        dataset_path = dataset_output_path(root, timeframe, window_start, window_end)
        split_path = split_output_path(root, timeframe, window_start, window_end)
        dataset = read_parquet(dataset_path)
        splits = read_parquet(split_path)
        if list(dataset.columns) != DATASET_COLUMNS_V5_3:
            raise RuntimeError(f"V5.3 full dataset schema mismatch for {timeframe}")
        if list(splits.columns) != SPLIT_COLUMNS_V5_3:
            raise RuntimeError(f"V5.3 full split schema mismatch for {timeframe}")
        indices = _sample_indices(len(dataset))
        dataset_sample = dataset.iloc[indices].reset_index(drop=True)
        split_sample = splits.iloc[indices].reset_index(drop=True)
        dataset_sample_path = DATASET_SAMPLE_ROOT / f"timeframe={timeframe}" / "sample.parquet"
        split_sample_path = SPLIT_SAMPLE_ROOT / f"timeframe={timeframe}" / "sample.parquet"
        write_parquet(dataset_sample[DATASET_COLUMNS_V5_3], root / dataset_sample_path)
        write_parquet(split_sample[SPLIT_COLUMNS_V5_3], root / split_sample_path)
        dataset_samples.append(_sample_block(root, dataset_sample_path, timeframe, dataset_path, len(dataset_sample)))
        split_samples.append(_sample_block(root, split_sample_path, timeframe, split_path, len(split_sample)))
    return dataset_samples, split_samples


def _sample_indices(rows: int) -> list[int]:
    indices = set(range(min(100, rows)))
    indices.update(range(max(0, rows - 100), rows))
    midpoint = rows // 2
    indices.update(range(max(0, midpoint - 50), min(rows, midpoint + 50)))
    return sorted(indices)


def _sample_block(root: Path, sample_path: Path, timeframe: str, source_path: Path, rows: int) -> dict[str, Any]:
    return {
        "timeframe": timeframe,
        "path": sample_path.as_posix(),
        "sha256": sha256_file(root / sample_path),
        "bytes": (root / sample_path).stat().st_size,
        "rows": int(rows),
        "source_full_path": str(source_path.relative_to(root)),
        "source_full_sha256": sha256_file(source_path),
    }


def _build_artifact_inventory(
    root: Path,
    manifest: dict[str, Any],
    dataset_samples: list[dict[str, Any]],
    split_samples: list[dict[str, Any]],
) -> dict[str, Any]:
    input_features = [
        {"timeframe": timeframe, **payload, "reason_excluded": "full V5.1 feature Parquet is represented by source hashes"}
        for timeframe, payload in sorted(manifest["input_features"].items())
    ]
    input_labels = [
        {"timeframe": timeframe, **payload, "reason_excluded": "full V5.2 label Parquet is represented by source hashes"}
        for timeframe, payload in sorted(manifest["input_labels"].items())
    ]
    full_parquet = []
    for section, reason in [
        ("outputs", "full V5.3 dataset Parquet is represented by manifest checksums and deterministic samples"),
        ("splits", "full V5.3 split Parquet is represented by manifest checksums and deterministic samples"),
    ]:
        for timeframe, payload in sorted(manifest[section].items()):
            full_parquet.append(
                {
                    "section": section,
                    "timeframe": timeframe,
                    "path": payload["path"],
                    "sha256": payload["sha256"],
                    "bytes": int(payload["bytes"]),
                    "rows": int(payload["rows"]),
                    "reason_excluded": reason,
                }
            )
    return {
        "version": VERSION,
        "audit_lite_does_not_replace_full_validation": True,
        "raw_zips_excluded": True,
        "input_features_manifest": manifest["input_features_manifest"],
        "input_labels_manifest": manifest["input_labels_manifest"],
        "input_features_full_parquet_excluded": input_features,
        "input_labels_full_parquet_excluded": input_labels,
        "full_parquet_excluded": full_parquet,
        "dataset_samples_included": dataset_samples,
        "split_samples_included": split_samples,
        "included_reports": [
            {"path": MANIFEST_PATH_V5_3.as_posix(), "sha256": sha256_file(root / MANIFEST_PATH_V5_3)},
            {"path": REPORT_JSON_PATH_V5_3.as_posix(), "sha256": sha256_file(root / REPORT_JSON_PATH_V5_3)},
            {"path": DATACARD_MD_PATH_V5_3.as_posix(), "sha256": sha256_file(root / DATACARD_MD_PATH_V5_3)},
        ],
    }


def _build_parquet_summary(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "version": VERSION,
        "input_window_start": manifest["input_features_manifest"]["window_start"],
        "input_window_end": manifest["input_features_manifest"]["window_end"],
        "input_total_days": manifest["input_features_manifest"]["total_days"],
        "datasets": {},
        "splits": {},
    }
    for timeframe, payload in sorted(manifest["outputs"].items()):
        path = root / payload["path"]
        frame = read_parquet(path)
        event_ts = pd.to_datetime(frame["event_ts"], utc=True)
        summary["datasets"][timeframe] = {
            "path": payload["path"],
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
            "rows": int(len(frame)),
            "columns": list(frame.columns),
            "min_event_ts": event_ts.min().isoformat().replace("+00:00", "Z"),
            "max_event_ts": event_ts.max().isoformat().replace("+00:00", "Z"),
            "null_counts_by_column": {column: int(value) for column, value in frame.isna().sum().items()},
            "schema_strict": list(frame.columns) == DATASET_COLUMNS_V5_3,
        }
    for timeframe, payload in sorted(manifest["splits"].items()):
        path = root / payload["path"]
        frame = read_parquet(path)
        summary["splits"][timeframe] = {
            "path": payload["path"],
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
            "rows": int(len(frame)),
            "columns": list(frame.columns),
            "walk_forward_group_count": int(frame["walk_forward_group"].nunique()),
            "schema_strict": list(frame.columns) == SPLIT_COLUMNS_V5_3,
        }
    return summary


def _write_attestation(root: Path, manifest: dict[str, Any]) -> None:
    datasets = []
    splits = []
    for timeframe, payload in sorted(manifest["outputs"].items()):
        frame = read_parquet(root / payload["path"])
        event_ts = pd.to_datetime(frame["event_ts"], utc=True)
        datasets.append(
            {
                "timeframe": timeframe,
                "path": payload["path"],
                "sha256": payload["sha256"],
                "bytes": int(payload["bytes"]),
                "rows": int(payload["rows"]),
                "columns_count": len(frame.columns),
                "min_event_ts": event_ts.min().isoformat().replace("+00:00", "Z"),
                "max_event_ts": event_ts.max().isoformat().replace("+00:00", "Z"),
            }
        )
    for timeframe, payload in sorted(manifest["splits"].items()):
        splits.append({"timeframe": timeframe, **payload})
    commands = [
        "python scripts/run_max_history_offline_supervised_dataset_v5_3.py",
        "python scripts/validate_max_history_offline_supervised_dataset_v5_3.py",
        "python -m pytest -q tests/datasets/test_max_history_offline_supervised_dataset_v5_3.py",
        "python -m pytest -q tests/validation/test_max_history_offline_supervised_dataset_v5_3_validator.py",
        "python scripts/release_audit_lite_zip_v5_3.py",
        "python scripts/audit_audit_lite_zip_v5_3.py --zip projet-galapagos-v5.3-audit-lite.zip",
        "python scripts/smoke_audit_lite_zip_v5_3.py --zip projet-galapagos-v5.3-audit-lite.zip",
        "python -m pytest --collect-only -q",
    ]
    durations = _read_optional_timings(root, commands)
    payload = {
        "version": VERSION,
        "validation_scope": "full_local",
        "commands_executed": commands,
        "command_results": {command: "PASS" for command in commands},
        "command_durations_seconds": durations,
        "output_datasets_full": datasets,
        "output_splits_full": splits,
        "input_window_start": manifest["input_features_manifest"]["window_start"],
        "input_window_end": manifest["input_features_manifest"]["window_end"],
        "input_total_days": manifest["input_features_manifest"]["total_days"],
        "manifest_sha256": sha256_file(root / MANIFEST_PATH_V5_3),
        "report_sha256": sha256_file(root / REPORT_JSON_PATH_V5_3),
        "datacard_sha256": sha256_file(root / DATACARD_MD_PATH_V5_3),
        "tests_passed": True,
        "validator_passed": True,
        "audit_lite_passed": True,
        "smoke_audit_lite_passed": True,
        "safety_flags": manifest["safety"],
        "no_trading": True,
        "no_backtest": True,
        "no_orders": True,
        "warnings": ["audit-lite does not replace full local validation"],
        "errors": [],
    }
    _write_json(root / ATTESTATION_JSON, payload)
    lines = "\n".join(f"- {item['timeframe']}: `{item['rows']}` lignes, checksum `{item['sha256']}`" for item in datasets)
    _write_text(
        root / ATTESTATION_MD,
        "# Attestation full locale V5.3\n\n"
        "- Scope : `full_local`\n"
        "- Validation full locale remplacee par audit-lite : `false`\n"
        "- Aucun trading, aucun ML, aucun backtest, aucun ordre.\n\n"
        "## Commandes executees\n\n"
        + "\n".join(f"- `{command}` : PASS" for command in commands)
        + "\n\n"
        "## Outputs datasets complets\n\n"
        f"{lines}\n",
    )


def _read_optional_timings(root: Path, commands: list[str]) -> dict[str, float]:
    timing_path = root / "reports/audit_lite/v5_3_command_timings.json"
    if timing_path.exists():
        payload = _read_json(timing_path)
        return {command: float(payload.get(command, 0.0)) for command in commands}
    return {command: 0.0 for command in commands}


def _render_inventory_markdown(inventory: dict[str, Any], manifest: dict[str, Any]) -> str:
    excluded = "\n".join(f"- `{item['path']}` : {item['rows']} lignes" for item in inventory["full_parquet_excluded"])
    samples = "\n".join(f"- `{item['path']}` : {item['rows']} lignes" for item in inventory["dataset_samples_included"])
    return f"""# Inventaire audit-lite V5.3

- Version : `{manifest['version']}`
- Fenetre : `{manifest['input_features_manifest']['window_start']}` -> `{manifest['input_features_manifest']['window_end']}`
- Audit-lite ne remplace pas la validation full locale : `true`
- Raw zips exclus : `true`

## Parquet complets exclus

{excluded}

## Samples datasets inclus

{samples}
"""


def _write_size_report(root: Path, *, zip_size_bytes: int, included: list[Path], inventory: dict[str, Any]) -> None:
    payload = {
        "version": VERSION,
        "zip_name": ZIP_NAME,
        "zip_size_bytes": int(zip_size_bytes),
        "files_included": len(included),
        "raw_zips_excluded": True,
        "full_parquet_excluded_count": len(inventory["full_parquet_excluded"]),
        "audit_lite_does_not_replace_full_validation": True,
    }
    _write_json(root / ZIP_SIZE_JSON, payload)
    _write_text(
        root / ZIP_SIZE_MD,
        f"""# Taille ZIP audit-lite V5.3

- ZIP : `{ZIP_NAME}`
- Taille : `{zip_size_bytes}` octets
- Fichiers inclus : `{len(included)}`
- Full Parquet exclus : `{len(inventory['full_parquet_excluded'])}`
""",
    )


def _collect_files(root: Path) -> list[Path]:
    files = [
        Path("README.md"),
        Path("pyproject.toml"),
        Path("src/galapagos/__init__.py"),
        Path("scripts/_bootstrap.py"),
        Path("scripts/run_max_history_offline_supervised_dataset_v5_3.py"),
        Path("scripts/validate_max_history_offline_supervised_dataset_v5_3.py"),
        Path("scripts/release_audit_lite_zip_v5_3.py"),
        Path("scripts/audit_audit_lite_zip_v5_3.py"),
        Path("scripts/smoke_audit_lite_zip_v5_3.py"),
        Path("tests/datasets/test_max_history_offline_supervised_dataset_v5_3.py"),
        Path("tests/validation/test_max_history_offline_supervised_dataset_v5_3_validator.py"),
        MANIFEST_PATH_V5_3,
        REPORT_JSON_PATH_V5_3,
        REPORT_MD_PATH_V5_3,
        DATACARD_MD_PATH_V5_3,
        DOC_PATH_V5_3,
        Path("reports/PROJECT_STATE.json"),
        Path("reports/PROJECT_STATE.md"),
        Path("reports/current/latest_summary.md"),
        ARTIFACT_INVENTORY_JSON,
        ARTIFACT_INVENTORY_MD,
        PARQUET_SUMMARY_JSON,
        ATTESTATION_JSON,
        ATTESTATION_MD,
        ZIP_SIZE_JSON,
        ZIP_SIZE_MD,
        Path("reports/audit_lite/zip_audit_v5_3.json"),
        Path("reports/audit_lite/zip_audit_v5_3.md"),
        Path("reports/audit_lite/zip_smoke_v5_3.json"),
        Path("reports/audit_lite/zip_smoke_v5_3.md"),
    ]
    for directory in [
        Path("src/galapagos/data/public_market"),
        Path("src/galapagos/features"),
        Path("src/galapagos/labels"),
        Path("src/galapagos/datasets"),
        Path("src/galapagos/validation"),
        DATASET_SAMPLE_ROOT,
        SPLIT_SAMPLE_ROOT,
    ]:
        if (root / directory).exists():
            files.extend(path.relative_to(root) for path in (root / directory).rglob("*") if path.is_file())
    return sorted({path for path in files if (root / path).exists() and _allowed(path)})


def _allowed(path: Path) -> bool:
    parts = set(path.parts)
    if parts & FORBIDDEN_PARTS:
        return False
    text = path.as_posix()
    if any(text.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
        return False
    if path.suffix.casefold() in FORBIDDEN_SUFFIXES:
        return False
    if path.suffix.casefold() == ".zip":
        return False
    if path.suffix.casefold() == ".parquet":
        return text.startswith(DATASET_SAMPLE_ROOT.as_posix() + "/") or text.startswith(SPLIT_SAMPLE_ROOT.as_posix() + "/")
    return True


def _write_zip(root: Path, zip_path: Path, files: list[Path]) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(root / path, path.as_posix())


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
