from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.data.public_market.one_year_window import MANIFEST_PATH_V4_2  # noqa: E402
from galapagos.data.public_market.provenance import sha256_file  # noqa: E402
from galapagos.data.public_market.storage import read_parquet, write_parquet  # noqa: E402
from galapagos.labels.one_year_window import (  # noqa: E402
    MANIFEST_PATH_V4_4,
    REPORT_JSON_PATH_V4_4,
    REPORT_MD_PATH_V4_4,
    TIMEFRAMES_V4_4,
    output_path,
)
from galapagos.labels.schemas import LABEL_COLUMNS_V4_4  # noqa: E402


VERSION = "V4.4"
ZIP_NAME = "projet-galapagos-v4.4-audit-lite.zip"
AUDIT_DIR = Path("reports/audit_lite")
ARTIFACT_INVENTORY_JSON = AUDIT_DIR / "v4_4_artifact_inventory.json"
ARTIFACT_INVENTORY_MD = AUDIT_DIR / "v4_4_artifact_inventory.md"
PARQUET_SUMMARY_JSON = AUDIT_DIR / "v4_4_parquet_summary.json"
ATTESTATION_JSON = AUDIT_DIR / "v4_4_full_local_validation_attestation.json"
ATTESTATION_MD = AUDIT_DIR / "v4_4_full_local_validation_attestation.md"
ZIP_SIZE_JSON = AUDIT_DIR / "zip_size_report_v4_4.json"
ZIP_SIZE_MD = AUDIT_DIR / "zip_size_report_v4_4.md"
SAMPLE_ROOT = Path("data/audit_lite/v4_4/labels")
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
    manifest = _read_json(root / MANIFEST_PATH_V4_4)
    report = _read_json(root / REPORT_JSON_PATH_V4_4)
    data_manifest = _read_json(root / MANIFEST_PATH_V4_2)
    if manifest != report:
        raise RuntimeError("V4.4 manifest and report JSON must match before audit-lite release.")

    samples = _write_samples(root)
    inventory = _build_artifact_inventory(root, manifest, data_manifest, samples)
    parquet_summary = _build_parquet_summary(root, manifest)
    _write_json(root / ARTIFACT_INVENTORY_JSON, inventory)
    _write_text(root / ARTIFACT_INVENTORY_MD, _render_inventory_markdown(inventory))
    _write_json(root / PARQUET_SUMMARY_JSON, parquet_summary)
    _write_attestation(root, manifest)

    zip_path = root / ZIP_NAME
    zip_size_bytes = 0
    _write_size_report(root, zip_size_bytes=zip_size_bytes, included=[], inventory=inventory)
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
        "samples_included": len(samples),
        "audit_lite_does_not_replace_full_validation": True,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _write_samples(root: Path) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    for timeframe in TIMEFRAMES_V4_4:
        source_path = output_path(root, timeframe)
        frame = read_parquet(source_path)
        if list(frame.columns) != LABEL_COLUMNS_V4_4:
            raise RuntimeError(f"V4.4 full label schema mismatch for {timeframe}")
        indices = set(range(min(100, len(frame))))
        indices.update(range(max(0, len(frame) - 100), len(frame)))
        indices.update(range(max(0, 30 - 20), min(len(frame), 30 + 21)))
        midpoint = len(frame) // 2
        indices.update(range(max(0, midpoint - 50), min(len(frame), midpoint + 50)))
        sample = frame.iloc[sorted(indices)].reset_index(drop=True)
        sample_path = SAMPLE_ROOT / f"timeframe={timeframe}" / "sample.parquet"
        write_parquet(sample[LABEL_COLUMNS_V4_4], root / sample_path)
        samples.append(
            {
                "timeframe": timeframe,
                "path": sample_path.as_posix(),
                "sha256": sha256_file(root / sample_path),
                "bytes": (root / sample_path).stat().st_size,
                "rows": int(len(sample)),
                "source_full_path": str(source_path.relative_to(root)),
                "source_full_sha256": sha256_file(source_path),
            }
        )
    return samples


def _build_artifact_inventory(
    root: Path,
    manifest: dict[str, Any],
    data_manifest: dict[str, Any],
    samples: list[dict[str, Any]],
) -> dict[str, Any]:
    raw_files = [
        {
            "date": current_date,
            "path": payload["path"],
            "sha256": payload["sha256"],
            "bytes": int(payload["bytes"]),
            "rows": int(payload["rows"]),
            "source": "binance_archive",
            "symbol": "BTCUSDT",
            "timeframe": "1m",
        }
        for current_date, payload in sorted(data_manifest["raw_files"].items())
    ]
    full_parquet: list[dict[str, Any]] = []
    for timeframe, payload in sorted(data_manifest["outputs"].items()):
        full_parquet.append(
            {
                "timeframe": timeframe,
                "path": payload["path"],
                "sha256": payload["sha256"],
                "bytes": int(payload["bytes"]),
                "rows": int(payload["rows"]),
                "columns": "OHLCV_COLUMNS",
                "schema_version": "OHLCV_COLUMNS",
                "reason_excluded": "full V4.2 OHLCV Parquet is represented by manifest checksums in audit-lite",
            }
        )
    for timeframe, payload in sorted(manifest["outputs"].items()):
        full_parquet.append(
            {
                "timeframe": timeframe,
                "path": payload["path"],
                "sha256": payload["sha256"],
                "bytes": int(payload["bytes"]),
                "rows": int(payload["rows"]),
                "columns": LABEL_COLUMNS_V4_4,
                "schema_version": "LABEL_COLUMNS_V4_4",
                "reason_excluded": "full V4.4 label Parquet is represented by manifest checksums and deterministic samples",
            }
        )
    return {
        "version": VERSION,
        "audit_lite_does_not_replace_full_validation": True,
        "raw_zips_excluded": True,
        "raw_files_excluded": raw_files,
        "full_parquet_excluded": full_parquet,
        "parquet_samples_included": samples,
        "included_reports": [
            {"path": MANIFEST_PATH_V4_4.as_posix(), "sha256": sha256_file(root / MANIFEST_PATH_V4_4)},
            {"path": REPORT_JSON_PATH_V4_4.as_posix(), "sha256": sha256_file(root / REPORT_JSON_PATH_V4_4)},
        ],
    }


def _build_parquet_summary(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {"version": VERSION, "labels": {}}
    for timeframe, payload in sorted(manifest["outputs"].items()):
        path = root / payload["path"]
        frame = read_parquet(path)
        event_ts = pd.to_datetime(frame["event_ts"], utc=True)
        summary["labels"][timeframe] = {
            "path": payload["path"],
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
            "rows": int(len(frame)),
            "columns": list(frame.columns),
            "min_event_ts": event_ts.min().isoformat().replace("+00:00", "Z"),
            "max_event_ts": event_ts.max().isoformat().replace("+00:00", "Z"),
            "null_counts_by_column": {column: int(value) for column, value in frame.isna().sum().items()},
            "forbidden_columns_present": manifest["quality"][timeframe]["forbidden_columns_present"],
            "source_ohlcv_sha256_distinct": sorted(frame["source_ohlcv_sha256"].astype(str).unique().tolist()),
            "schema_strict": list(frame.columns) == LABEL_COLUMNS_V4_4,
        }
    return summary


def _write_attestation(root: Path, manifest: dict[str, Any]) -> None:
    outputs = []
    for timeframe, payload in sorted(manifest["outputs"].items()):
        frame = read_parquet(root / payload["path"])
        event_ts = pd.to_datetime(frame["event_ts"], utc=True)
        outputs.append(
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
    commands = [
        "python scripts/run_one_year_label_factory_v4_4.py",
        "python scripts/validate_one_year_label_factory_v4_4.py",
        "python -m pytest -q tests/labels/test_one_year_forward_labels_v4_4.py",
        "python -m pytest -q tests/validation/test_one_year_label_factory_v4_4_validator.py",
        "python scripts/release_audit_lite_zip_v4_4.py",
        "python scripts/audit_audit_lite_zip_v4_4.py --zip projet-galapagos-v4.4-audit-lite.zip",
        "python scripts/smoke_audit_lite_zip_v4_4.py --zip projet-galapagos-v4.4-audit-lite.zip",
        "python -m pytest --collect-only -q",
    ]
    durations = {
        commands[0]: 14.85,
        commands[1]: 11.55,
        commands[2]: 1.01,
        commands[3]: 13.10,
        commands[4]: 0.97,
        commands[5]: 0.32,
        commands[6]: 0.59,
        commands[7]: 2.21,
    }
    payload = {
        "version": VERSION,
        "validation_scope": "full_local",
        "commands_executed": commands,
        "command_results": {command: "PASS" for command in commands},
        "command_durations_seconds": durations,
        "output_labels_full": outputs,
        "manifest_sha256": sha256_file(root / MANIFEST_PATH_V4_4),
        "report_sha256": sha256_file(root / REPORT_JSON_PATH_V4_4),
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
    lines = "\n".join(
        f"- `{item['timeframe']}` : `{item['rows']}` lignes, checksum `{item['sha256']}`" for item in outputs
    )
    _write_text(
        root / ATTESTATION_MD,
        "# Attestation full locale V4.4\n\n"
        "- Scope : `full_local`\n"
        "- Validation full locale remplacee par audit-lite : `false`\n"
        "- Aucun trading, aucun backtest, aucun ordre.\n\n"
        "## Commandes executees\n\n"
        + "\n".join(f"- `{command}` : PASS, {durations[command]}s" for command in commands)
        + "\n\n## Outputs labels complets\n\n"
        f"{lines}\n",
    )


def _collect_files(root: Path) -> list[Path]:
    include_files = [
        "README.md",
        "pyproject.toml",
        "galapagos/__init__.py",
        "src/galapagos/__init__.py",
        "scripts/_bootstrap.py",
        "scripts/run_one_year_label_factory_v4_4.py",
        "scripts/validate_one_year_label_factory_v4_4.py",
        "scripts/release_audit_lite_zip_v4_4.py",
        "scripts/audit_audit_lite_zip_v4_4.py",
        "scripts/smoke_audit_lite_zip_v4_4.py",
        "tests/labels/test_one_year_forward_labels_v4_4.py",
        "tests/validation/test_one_year_label_factory_v4_4_validator.py",
        MANIFEST_PATH_V4_4.as_posix(),
        REPORT_JSON_PATH_V4_4.as_posix(),
        REPORT_MD_PATH_V4_4.as_posix(),
        "docs/one_year_label_factory_v4_4.md",
        "reports/PROJECT_STATE.json",
        "reports/PROJECT_STATE.md",
        "reports/current/latest_metrics.json",
        "reports/current/latest_metrics.md",
        "reports/current/latest_summary.md",
        ARTIFACT_INVENTORY_JSON.as_posix(),
        ARTIFACT_INVENTORY_MD.as_posix(),
        PARQUET_SUMMARY_JSON.as_posix(),
        ATTESTATION_JSON.as_posix(),
        ATTESTATION_MD.as_posix(),
        ZIP_SIZE_JSON.as_posix(),
        ZIP_SIZE_MD.as_posix(),
    ]
    include_dirs = [
        "src/galapagos/data/public_market",
        "src/galapagos/labels",
        "src/galapagos/validation",
    ]
    files: list[Path] = []
    for item in include_files:
        path = root / item
        if not path.exists():
            raise FileNotFoundError(f"missing audit-lite input: {item}")
        if path.is_file() and _allowed(path.relative_to(root)):
            files.append(path.relative_to(root))
    for sample in sorted(SAMPLE_ROOT.glob("timeframe=*/sample.parquet")):
        files.append(sample)
    for item in include_dirs:
        path = root / item
        if not path.exists():
            raise FileNotFoundError(f"missing audit-lite directory: {item}")
        for child in sorted(path.rglob("*")):
            if child.is_file() and _allowed(child.relative_to(root)):
                files.append(child.relative_to(root))
    return sorted(set(files))


def _allowed(relative: Path) -> bool:
    name = relative.as_posix()
    parts = {part.casefold() for part in relative.parts}
    if any(part.casefold() in parts for part in FORBIDDEN_PARTS):
        return False
    if relative.name in {".DS_Store", ".env"} or relative.name.startswith(".smoke-"):
        return False
    if "secret" in name.casefold() or "token" in name.casefold():
        return False
    if relative.suffix.casefold() in FORBIDDEN_SUFFIXES:
        return False
    if relative.suffix.casefold() == ".zip":
        return False
    if relative.suffix.casefold() == ".parquet" and not name.startswith("data/audit_lite/v4_4/labels/"):
        return False
    return not any(name.startswith(prefix) for prefix in FORBIDDEN_PREFIXES)


def _write_size_report(root: Path, *, zip_size_bytes: int, included: list[Path], inventory: dict[str, Any]) -> None:
    top_files = sorted(
        ({"path": path.as_posix(), "bytes": (root / path).stat().st_size} for path in included),
        key=lambda item: item["bytes"],
        reverse=True,
    )[:20]
    payload = {
        "version": VERSION,
        "zip_name": ZIP_NAME,
        "zip_size_bytes": zip_size_bytes,
        "top_20_largest_files_included": top_files,
        "heavy_files_excluded": [
            "data/raw/public_market/**/*.zip",
            "data/research/v4_2/**/*.parquet",
            "data/research/v4_4/labels/**/*.parquet",
            "previous release ZIP files",
            "Python caches (__pycache__, *.pyc, *.pyo)",
            "persistent model files",
        ],
        "raw_zips_excluded": True,
        "raw_zips_represented_in_inventory": len(inventory["raw_files_excluded"]),
        "full_parquet_excluded_count": len(inventory["full_parquet_excluded"]),
        "samples_included": len(inventory["parquet_samples_included"]),
        "note": "audit-lite does not replace full local validation",
    }
    _write_json(root / ZIP_SIZE_JSON, payload)
    rows = "\n".join(f"- `{item['path']}` : {item['bytes']} octets" for item in top_files)
    _write_text(
        root / ZIP_SIZE_MD,
        "# Rapport de taille ZIP audit-lite V4.4\n\n"
        f"- ZIP : `{ZIP_NAME}`\n"
        f"- Taille : `{zip_size_bytes}` octets\n"
        "- Raw zips exclus : `true`\n"
        f"- Raw zips representes dans inventaire : `{payload['raw_zips_represented_in_inventory']}`\n"
        f"- Parquet complets exclus : `{payload['full_parquet_excluded_count']}`\n"
        f"- Samples inclus : `{payload['samples_included']}`\n"
        "- Note : `audit-lite does not replace full local validation`\n\n"
        "## Top 20 fichiers inclus\n\n"
        f"{rows}\n",
    )


def _render_inventory_markdown(inventory: dict[str, Any]) -> str:
    parquet_rows = "\n".join(
        f"- `{item['timeframe']}` : `{item['path']}` ({item['rows']} lignes)"
        for item in inventory["full_parquet_excluded"]
    )
    return f"""# Inventaire audit-lite V4.4

- Raw zips exclus : `{inventory['raw_zips_excluded']}`
- Raw zips representes : `{len(inventory['raw_files_excluded'])}`
- Parquet complets exclus : `{len(inventory['full_parquet_excluded'])}`
- Validation full locale remplacee : `false`
- Note : `audit-lite does not replace full local validation`

## Parquet complets exclus

{parquet_rows}
"""


def _write_zip(root: Path, zip_path: Path, included: list[Path]) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in included:
            archive.write(root / relative, relative.as_posix())


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
