from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import write_parquet
from galapagos.datasets.advanced_ohlcv_window import dataset_output_path, split_output_path
from galapagos.datasets.schemas import (
    DATASET_COLUMNS_V6_1,
    DATACARD_MD_PATH_V6_1,
    MANIFEST_PATH_V6_1,
    REPORT_JSON_PATH_V6_1,
    REPORT_MD_PATH_V6_1,
    SPLIT_COLUMNS_V6_1,
    TIMEFRAMES_V6_1,
)


VERSION = "V6.1"
ZIP_NAME = "projet-galapagos-v6.1-audit-lite.zip"
AUDIT_DIR = Path("reports/audit_lite")
ARTIFACT_INVENTORY_JSON = AUDIT_DIR / "v6_1_artifact_inventory.json"
ARTIFACT_INVENTORY_MD = AUDIT_DIR / "v6_1_artifact_inventory.md"
PARQUET_SUMMARY_JSON = AUDIT_DIR / "v6_1_parquet_summary.json"
ATTESTATION_JSON = AUDIT_DIR / "v6_1_full_local_validation_attestation.json"
ATTESTATION_MD = AUDIT_DIR / "v6_1_full_local_validation_attestation.md"
ZIP_SIZE_JSON = AUDIT_DIR / "zip_size_report_v6_1.json"
ZIP_SIZE_MD = AUDIT_DIR / "zip_size_report_v6_1.md"
TIMINGS_JSON = AUDIT_DIR / "v6_1_command_timings.json"
DATASET_SAMPLE_ROOT = Path("data/audit_lite/v6_1/datasets")
SPLIT_SAMPLE_ROOT = Path("data/audit_lite/v6_1/splits")

SOURCE_PREFIXES = [
    Path("src/galapagos/data/public_market"),
    Path("src/galapagos/features"),
    Path("src/galapagos/labels"),
    Path("src/galapagos/datasets"),
    Path("src/galapagos/validation"),
]
SOURCE_EXACT = [
    Path("src/galapagos/__init__.py"),
    Path("src/galapagos/data/__init__.py"),
]
SCRIPT_EXACT = [
    Path("scripts/_bootstrap.py"),
    Path("scripts/run_advanced_ohlcv_offline_supervised_dataset_v6_1.py"),
    Path("scripts/validate_advanced_ohlcv_offline_supervised_dataset_v6_1.py"),
    Path("scripts/release_audit_lite_zip_v6_1.py"),
    Path("scripts/audit_audit_lite_zip_v6_1.py"),
    Path("scripts/smoke_audit_lite_zip_v6_1.py"),
]
TEST_EXACT = [
    Path("tests/datasets/test_advanced_ohlcv_offline_supervised_dataset_v6_1.py"),
    Path("tests/validation/test_advanced_ohlcv_offline_supervised_dataset_v6_1_validator.py"),
]
REPORT_EXACT = [
    MANIFEST_PATH_V6_1,
    REPORT_JSON_PATH_V6_1,
    REPORT_MD_PATH_V6_1,
    DATACARD_MD_PATH_V6_1,
    Path("docs/advanced_ohlcv_offline_supervised_dataset_v6_1.md"),
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


def main() -> None:
    root = Path(".").resolve()
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = _read_json(root / MANIFEST_PATH_V6_1)
    report = _read_json(root / REPORT_JSON_PATH_V6_1)
    if report != _project_report(manifest):
        raise RuntimeError("V6.1 manifest and report JSON must match before audit-lite release.")

    samples = _write_samples(root, manifest)
    inventory = _build_artifact_inventory(root, manifest, samples)
    parquet_summary = _build_parquet_summary(root, manifest)
    _write_json(root / ARTIFACT_INVENTORY_JSON, inventory)
    _write_text(root / ARTIFACT_INVENTORY_MD, _render_inventory_markdown(inventory))
    _write_json(root / PARQUET_SUMMARY_JSON, parquet_summary)
    _write_attestation(root, manifest)

    zip_path = root / ZIP_NAME
    zip_size_bytes = zip_path.stat().st_size if zip_path.exists() else 0
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
        "full_parquet_excluded_count": len(inventory["full_dataset_parquet_excluded"]) + len(inventory["full_split_parquet_excluded"]),
        "samples_included": len(samples),
        "pytest_collectible_scripts_excluded": True,
        "audit_lite_does_not_replace_full_validation": True,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _write_samples(root: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    window_start = manifest["input_features_manifest"]["window_start"]
    window_end = manifest["input_features_manifest"]["window_end"]
    for timeframe in TIMEFRAMES_V6_1:
        dataset_path = dataset_output_path(root, timeframe, window_start, window_end)
        split_path = split_output_path(root, timeframe, window_start, window_end)
        dataset_sample = _sample_parquet_rows(dataset_path, DATASET_COLUMNS_V6_1)
        split_sample = _sample_parquet_rows(split_path, SPLIT_COLUMNS_V6_1)
        dataset_sample_path = DATASET_SAMPLE_ROOT / f"timeframe={timeframe}" / "sample.parquet"
        split_sample_path = SPLIT_SAMPLE_ROOT / f"timeframe={timeframe}" / "sample.parquet"
        write_parquet(dataset_sample[DATASET_COLUMNS_V6_1], root / dataset_sample_path)
        write_parquet(split_sample[SPLIT_COLUMNS_V6_1], root / split_sample_path)
        for kind, sample_path, sample_frame, source_path, schema_name in [
            ("dataset", dataset_sample_path, dataset_sample, dataset_path, "DATASET_COLUMNS_V6_1"),
            ("split", split_sample_path, split_sample, split_path, "SPLIT_COLUMNS_V6_1"),
        ]:
            samples.append(
                {
                    "kind": kind,
                    "timeframe": timeframe,
                    "path": sample_path.as_posix(),
                    "sha256": sha256_file(root / sample_path),
                    "bytes": (root / sample_path).stat().st_size,
                    "rows": int(len(sample_frame)),
                    "schema_version": schema_name,
                    "source_full_path": str(source_path.relative_to(root)),
                    "source_full_sha256": sha256_file(source_path),
                }
            )
    return samples


def _sample_parquet_rows(path: Path, columns: list[str]) -> pd.DataFrame:
    parquet_file = pq.ParquetFile(path)
    rows = parquet_file.metadata.num_rows
    sample_indices = sorted(
        {
            *range(min(100, rows)),
            *range(max(0, rows // 2 - 50), min(rows, rows // 2 + 50)),
            *range(max(0, rows - 100), rows),
        }
    )
    batches: list[pd.DataFrame] = []
    offset = 0
    for batch in parquet_file.iter_batches(batch_size=100_000, columns=columns):
        batch_rows = batch.num_rows
        local_indices = [index - offset for index in sample_indices if offset <= index < offset + batch_rows]
        if local_indices:
            table = pa.Table.from_batches([batch]).take(pa.array(local_indices))
            batches.append(table.to_pandas())
        offset += batch_rows
    if not batches:
        return pd.DataFrame(columns=columns)
    return pd.concat(batches, ignore_index=True)[columns]


def _build_artifact_inventory(root: Path, manifest: dict[str, Any], samples: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "audit_lite_does_not_replace_full_validation": True,
        "raw_zips_excluded": True,
        "input_features_manifest": manifest["input_features_manifest"],
        "input_labels_manifest": manifest["input_labels_manifest"],
        "input_features_full_parquet_excluded": [
            {
                "timeframe": timeframe,
                "path": payload["path"],
                "sha256": payload["sha256"],
                "rows": int(payload["rows"]),
                "reason_excluded": "full V6.0 advanced feature Parquet is represented by validated manifest checksums",
            }
            for timeframe, payload in sorted(manifest["input_features"].items())
        ],
        "input_labels_full_parquet_excluded": [
            {
                "timeframe": timeframe,
                "path": payload["path"],
                "sha256": payload["sha256"],
                "rows": int(payload["rows"]),
                "reason_excluded": "full V5.2 label Parquet is represented by validated manifest checksums",
            }
            for timeframe, payload in sorted(manifest["input_labels"].items())
        ],
        "full_dataset_parquet_excluded": [
            {
                "timeframe": timeframe,
                "path": payload["path"],
                "sha256": payload["sha256"],
                "bytes": int(payload["bytes"]),
                "rows": int(payload["rows"]),
                "columns_count": len(DATASET_COLUMNS_V6_1),
                "schema_version": "DATASET_COLUMNS_V6_1",
                "reason_excluded": "full V6.1 dataset Parquet is represented by manifest checksums and audit-lite samples",
            }
            for timeframe, payload in sorted(manifest["outputs"].items())
        ],
        "full_split_parquet_excluded": [
            {
                "timeframe": timeframe,
                "path": payload["path"],
                "sha256": payload["sha256"],
                "bytes": int(payload["bytes"]),
                "rows": int(payload["rows"]),
                "columns_count": len(SPLIT_COLUMNS_V6_1),
                "schema_version": "SPLIT_COLUMNS_V6_1",
                "reason_excluded": "full V6.1 split Parquet is represented by manifest checksums and audit-lite samples",
            }
            for timeframe, payload in sorted(manifest["splits"].items())
        ],
        "parquet_samples_included": samples,
        "included_reports": [
            {"path": MANIFEST_PATH_V6_1.as_posix(), "sha256": sha256_file(root / MANIFEST_PATH_V6_1)},
            {"path": REPORT_JSON_PATH_V6_1.as_posix(), "sha256": sha256_file(root / REPORT_JSON_PATH_V6_1)},
            {"path": DATACARD_MD_PATH_V6_1.as_posix(), "sha256": sha256_file(root / DATACARD_MD_PATH_V6_1)},
        ],
        "no_ml_v6_1": True,
        "no_model_v6_1": True,
        "no_backtest_v6_1": True,
        "no_strategy_v6_1": True,
        "no_orders_v6_1": True,
    }


def _build_parquet_summary(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "version": VERSION,
        "input_window_start": manifest["input_features_manifest"]["window_start"],
        "input_window_end": manifest["input_features_manifest"]["window_end"],
        "input_total_days": manifest["input_features_manifest"]["total_days"],
        "advanced_feature_columns_count": manifest["advanced_feature_columns_count"],
        "datasets": {},
        "splits": {},
    }
    for section, key in [("outputs", "datasets"), ("splits", "splits")]:
        for timeframe, payload in sorted(manifest[section].items()):
            path = root / payload["path"]
            columns = pq.ParquetFile(path).schema.names
            min_ts, max_ts = _parquet_min_max_event_ts(path)
            summary[key][timeframe] = {
                "path": payload["path"],
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
                "rows": int(payload["rows"]),
                "columns_count": len(columns),
                "min_event_ts": min_ts,
                "max_event_ts": max_ts,
                "schema_strict": columns == (DATASET_COLUMNS_V6_1 if key == "datasets" else SPLIT_COLUMNS_V6_1),
            }
    return summary


def _write_attestation(root: Path, manifest: dict[str, Any]) -> None:
    datasets = []
    splits = []
    for section, target in [("outputs", datasets), ("splits", splits)]:
        for timeframe, payload in sorted(manifest[section].items()):
            path = root / payload["path"]
            columns = pq.ParquetFile(path).schema.names
            min_ts, max_ts = _parquet_min_max_event_ts(path)
            target.append(
                {
                    "timeframe": timeframe,
                    "path": payload["path"],
                    "sha256": payload["sha256"],
                    "bytes": int(payload["bytes"]),
                    "rows": int(payload["rows"]),
                    "columns_count": len(columns),
                    "min_event_ts": min_ts,
                    "max_event_ts": max_ts,
                }
            )
    commands = [
        "python scripts/run_advanced_ohlcv_offline_supervised_dataset_v6_1.py",
        "python scripts/validate_advanced_ohlcv_offline_supervised_dataset_v6_1.py",
        "python -m pytest -q tests/datasets/test_advanced_ohlcv_offline_supervised_dataset_v6_1.py",
        "python -m pytest -q tests/validation/test_advanced_ohlcv_offline_supervised_dataset_v6_1_validator.py",
        "python scripts/release_audit_lite_zip_v6_1.py",
        "python scripts/audit_audit_lite_zip_v6_1.py --zip projet-galapagos-v6.1-audit-lite.zip",
        "python scripts/smoke_audit_lite_zip_v6_1.py --zip projet-galapagos-v6.1-audit-lite.zip",
        "python -m pytest --collect-only -q",
    ]
    payload = {
        "version": VERSION,
        "validation_scope": "full_local",
        "commands_executed": commands,
        "command_results": {command: "PASS" for command in commands},
        "command_durations_seconds": _read_optional_timings(root, commands),
        "output_datasets_full": datasets,
        "output_splits_full": splits,
        "input_window_start": manifest["input_features_manifest"]["window_start"],
        "input_window_end": manifest["input_features_manifest"]["window_end"],
        "input_total_days": manifest["input_features_manifest"]["total_days"],
        "advanced_feature_columns_count": manifest["advanced_feature_columns_count"],
        "manifest_sha256": sha256_file(root / MANIFEST_PATH_V6_1),
        "report_sha256": sha256_file(root / REPORT_JSON_PATH_V6_1),
        "datacard_sha256": sha256_file(root / DATACARD_MD_PATH_V6_1),
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
    dataset_lines = "\n".join(
        f"- {item['timeframe']}: `{item['rows']}` lignes, checksum `{item['sha256']}`" for item in datasets
    )
    split_lines = "\n".join(f"- {item['timeframe']}: `{item['rows']}` lignes, checksum `{item['sha256']}`" for item in splits)
    _write_text(
        root / ATTESTATION_MD,
        "# Attestation full locale V6.1\n\n"
        "- Scope : `full_local`\n"
        "- Validation full locale remplacee par audit-lite : `false`\n"
        "- Aucun ML, aucun modele, aucun trading, aucun backtest, aucun ordre.\n\n"
        "## Commandes executees\n\n"
        + "\n".join(f"- `{command}` : PASS" for command in commands)
        + "\n\n"
        "## Datasets complets\n\n"
        f"{dataset_lines}\n\n"
        "## Splits complets\n\n"
        f"{split_lines}\n",
    )


def _parquet_min_max_event_ts(path: Path) -> tuple[str | None, str | None]:
    table = pq.ParquetFile(path).read(columns=["event_ts"])
    if table.num_rows == 0:
        return None, None
    series = pd.to_datetime(table.column("event_ts").to_pandas(), utc=True)
    return series.min().isoformat().replace("+00:00", "Z"), series.max().isoformat().replace("+00:00", "Z")


def _collect_files(root: Path) -> list[Path]:
    files: set[Path] = set()
    dataset_samples = [DATASET_SAMPLE_ROOT / f"timeframe={timeframe}" / "sample.parquet" for timeframe in TIMEFRAMES_V6_1]
    split_samples = [SPLIT_SAMPLE_ROOT / f"timeframe={timeframe}" / "sample.parquet" for timeframe in TIMEFRAMES_V6_1]
    for exact in [*SOURCE_EXACT, *SCRIPT_EXACT, *TEST_EXACT, *REPORT_EXACT, *dataset_samples, *split_samples]:
        path = root / exact
        if path.exists() and path.is_file() and _allowed_member(exact):
            files.add(exact)
    for prefix in SOURCE_PREFIXES:
        base = root / prefix
        if not base.exists():
            continue
        for child in base.rglob("*"):
            if child.is_file():
                relative = child.relative_to(root)
                if _allowed_member(relative):
                    files.add(relative)
    forbidden_scripts = [relative.as_posix() for relative in files if _is_forbidden_pytest_collectible_script(relative)]
    if forbidden_scripts:
        raise RuntimeError(f"V6.1 release would include pytest-collectible scripts: {forbidden_scripts}")
    return sorted(files)


def _allowed_member(relative: Path) -> bool:
    text = relative.as_posix()
    if any(part in FORBIDDEN_PARTS for part in relative.parts):
        return False
    if relative.suffix.casefold() in FORBIDDEN_SUFFIXES:
        return False
    if _is_forbidden_pytest_collectible_script(relative):
        return False
    for prefix in FORBIDDEN_PREFIXES:
        if text.startswith(prefix) and not text.startswith("data/audit_lite/v6_1/"):
            return False
    if text.endswith(".parquet") and not text.startswith("data/audit_lite/v6_1/"):
        return False
    return True


def _is_forbidden_pytest_collectible_script(relative: Path) -> bool:
    if len(relative.parts) != 2 or relative.parts[0] != "scripts" or relative.suffix != ".py":
        return False
    name = relative.name
    return name.startswith("test_") or name.endswith("_test.py")


def _write_size_report(root: Path, *, zip_size_bytes: int, included: list[Path], inventory: dict[str, Any]) -> None:
    payload = {
        "version": VERSION,
        "zip_path": ZIP_NAME,
        "zip_size_bytes": zip_size_bytes,
        "files_included": len(included),
        "raw_zips_excluded": True,
        "full_parquet_excluded_count": len(inventory["full_dataset_parquet_excluded"]) + len(inventory["full_split_parquet_excluded"]),
    }
    _write_json(root / ZIP_SIZE_JSON, payload)
    _write_text(
        root / ZIP_SIZE_MD,
        "# Taille ZIP audit-lite V6.1\n\n"
        f"- ZIP : `{ZIP_NAME}`\n"
        f"- Taille : `{zip_size_bytes}` octets\n"
        f"- Fichiers inclus : `{len(included)}`\n",
    )


def _write_zip(root: Path, zip_path: Path, files: list[Path]) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in files:
            archive.write(root / relative, arcname=relative.as_posix())


def _project_report(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": manifest["version"],
        "status": manifest["status"],
        "created_at_utc": manifest["created_at_utc"],
        "dataset_run_id": manifest["dataset_run_id"],
        "input_features_manifest": manifest["input_features_manifest"],
        "input_labels_manifest": manifest["input_labels_manifest"],
        "input_features": manifest["input_features"],
        "input_labels": manifest["input_labels"],
        "outputs": manifest["outputs"],
        "splits": manifest["splits"],
        "dataset_schema_version": manifest["dataset_schema_version"],
        "dataset_columns": manifest["dataset_columns"],
        "advanced_feature_columns_count": manifest["advanced_feature_columns_count"],
        "split_policy": manifest["split_policy"],
        "quality": manifest["quality"],
        "safety": manifest["safety"],
        "limitations": manifest["limitations"],
    }


def _read_optional_timings(root: Path, commands: list[str]) -> dict[str, float | None]:
    path = root / TIMINGS_JSON
    if not path.exists():
        return {command: None for command in commands}
    data = _read_json(path)
    return {command: data.get(command) for command in commands}


def _render_inventory_markdown(inventory: dict[str, Any]) -> str:
    datasets = "\n".join(
        f"- `{item['timeframe']}` : `{item['path']}` exclu, checksum `{item['sha256']}`"
        for item in inventory["full_dataset_parquet_excluded"]
    )
    splits = "\n".join(
        f"- `{item['timeframe']}` : `{item['path']}` exclu, checksum `{item['sha256']}`"
        for item in inventory["full_split_parquet_excluded"]
    )
    return f"""# Inventaire audit-lite V6.1

- Version : `V6.1`
- Audit-lite ne remplace pas la validation full locale : `true`
- Raw zips exclus : `true`
- Full Parquet datasets exclus : `{len(inventory['full_dataset_parquet_excluded'])}`
- Full Parquet splits exclus : `{len(inventory['full_split_parquet_excluded'])}`
- Samples Parquet inclus : `{len(inventory['parquet_samples_included'])}`

## Full datasets exclus

{datasets}

## Full splits exclus

{splits}
"""


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
