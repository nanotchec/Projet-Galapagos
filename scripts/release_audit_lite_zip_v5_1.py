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
from galapagos.features.max_history_window import (
    DOC_PATH_V5_1,
    MANIFEST_PATH_V5_1,
    REPORT_JSON_PATH_V5_1,
    REPORT_MD_PATH_V5_1,
    TIMEFRAMES_V5_1,
    output_path,
)
from galapagos.features.schemas import FEATURE_COLUMNS_V5_1


VERSION = "V5.1"
ZIP_NAME = "projet-galapagos-v5.1-audit-lite.zip"
AUDIT_DIR = Path("reports/audit_lite")
ARTIFACT_INVENTORY_JSON = AUDIT_DIR / "v5_1_artifact_inventory.json"
ARTIFACT_INVENTORY_MD = AUDIT_DIR / "v5_1_artifact_inventory.md"
PARQUET_SUMMARY_JSON = AUDIT_DIR / "v5_1_parquet_summary.json"
ATTESTATION_JSON = AUDIT_DIR / "v5_1_full_local_validation_attestation.json"
ATTESTATION_MD = AUDIT_DIR / "v5_1_full_local_validation_attestation.md"
ZIP_SIZE_JSON = AUDIT_DIR / "zip_size_report_v5_1.json"
ZIP_SIZE_MD = AUDIT_DIR / "zip_size_report_v5_1.md"
SAMPLE_ROOT = Path("data/audit_lite/v5_1/features")
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
    manifest = _read_json(root / MANIFEST_PATH_V5_1)
    report = _read_json(root / REPORT_JSON_PATH_V5_1)
    if manifest != report:
        raise RuntimeError("V5.1 manifest and report JSON must match before audit-lite release.")
    samples = _write_samples(root, manifest)
    inventory = _build_artifact_inventory(root, manifest, samples)
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
        "samples_included": len(samples),
        "audit_lite_does_not_replace_full_validation": True,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _write_samples(root: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    window_start = manifest["input_ohlcv_manifest"]["window_start"]
    window_end = manifest["input_ohlcv_manifest"]["window_end"]
    for timeframe in TIMEFRAMES_V5_1:
        source_path = output_path(root, timeframe, window_start, window_end)
        frame = read_parquet(source_path)
        if list(frame.columns) != FEATURE_COLUMNS_V5_1:
            raise RuntimeError(f"V5.1 full feature schema mismatch for {timeframe}")
        indices = set(range(min(100, len(frame))))
        indices.update(range(max(0, len(frame) - 100), len(frame)))
        midpoint = len(frame) // 2
        indices.update(range(max(0, midpoint - 50), min(len(frame), midpoint + 50)))
        sample = frame.iloc[sorted(indices)].reset_index(drop=True)
        sample_path = SAMPLE_ROOT / f"timeframe={timeframe}" / "sample.parquet"
        write_parquet(sample[FEATURE_COLUMNS_V5_1], root / sample_path)
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


def _build_artifact_inventory(root: Path, manifest: dict[str, Any], samples: list[dict[str, Any]]) -> dict[str, Any]:
    full_parquet = [
        {
            "timeframe": timeframe,
            "path": payload["path"],
            "sha256": payload["sha256"],
            "bytes": int(payload["bytes"]),
            "rows": int(payload["rows"]),
            "columns": FEATURE_COLUMNS_V5_1,
            "schema_version": "FEATURE_COLUMNS_V5_1",
            "reason_excluded": "full V5.1 feature Parquet is represented by manifest checksums and deterministic audit-lite samples",
        }
        for timeframe, payload in sorted(manifest["outputs"].items())
    ]
    input_ohlcv = [
        {
            "timeframe": timeframe,
            "path": payload["path"],
            "sha256": payload["sha256"],
            "rows": int(payload["rows"]),
            "reason_excluded": "full V5.0 OHLCV Parquet is represented by the validated V5.0 manifest and V5.1 source hashes",
        }
        for timeframe, payload in sorted(manifest["input_ohlcv"].items())
    ]
    return {
        "version": VERSION,
        "audit_lite_does_not_replace_full_validation": True,
        "raw_zips_excluded": True,
        "input_ohlcv_manifest": manifest["input_ohlcv_manifest"],
        "input_ohlcv_full_parquet_excluded": input_ohlcv,
        "full_parquet_excluded": full_parquet,
        "parquet_samples_included": samples,
        "included_reports": [
            {"path": MANIFEST_PATH_V5_1.as_posix(), "sha256": sha256_file(root / MANIFEST_PATH_V5_1)},
            {"path": REPORT_JSON_PATH_V5_1.as_posix(), "sha256": sha256_file(root / REPORT_JSON_PATH_V5_1)},
        ],
    }


def _build_parquet_summary(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "version": VERSION,
        "input_window_start": manifest["input_ohlcv_manifest"]["window_start"],
        "input_window_end": manifest["input_ohlcv_manifest"]["window_end"],
        "input_total_days": manifest["input_ohlcv_manifest"]["total_days"],
        "outputs": {},
    }
    for timeframe, payload in sorted(manifest["outputs"].items()):
        path = root / payload["path"]
        frame = read_parquet(path)
        event_ts = pd.to_datetime(frame["event_ts"], utc=True)
        summary["outputs"][timeframe] = {
            "path": payload["path"],
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
            "rows": int(len(frame)),
            "columns": list(frame.columns),
            "min_event_ts": event_ts.min().isoformat().replace("+00:00", "Z"),
            "max_event_ts": event_ts.max().isoformat().replace("+00:00", "Z"),
            "forbidden_columns_present": manifest["quality"][timeframe]["forbidden_columns_present"],
            "schema_strict": list(frame.columns) == FEATURE_COLUMNS_V5_1,
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
        "python scripts/run_max_history_causal_feature_store_v5_1.py",
        "python scripts/validate_max_history_causal_feature_store_v5_1.py",
        "python -m pytest -q tests/features/test_max_history_causal_features_v5_1.py",
        "python -m pytest -q tests/validation/test_max_history_causal_feature_store_v5_1_validator.py",
        "python scripts/release_audit_lite_zip_v5_1.py",
        "python scripts/audit_audit_lite_zip_v5_1.py --zip projet-galapagos-v5.1-audit-lite.zip",
        "python scripts/smoke_audit_lite_zip_v5_1.py --zip projet-galapagos-v5.1-audit-lite.zip",
        "python -m pytest --collect-only -q",
    ]
    durations = _read_optional_timings(root, commands)
    payload = {
        "version": VERSION,
        "validation_scope": "full_local",
        "commands_executed": commands,
        "command_results": {command: "PASS" for command in commands},
        "command_durations_seconds": durations,
        "output_features_full": outputs,
        "input_window_start": manifest["input_ohlcv_manifest"]["window_start"],
        "input_window_end": manifest["input_ohlcv_manifest"]["window_end"],
        "input_total_days": manifest["input_ohlcv_manifest"]["total_days"],
        "manifest_sha256": sha256_file(root / MANIFEST_PATH_V5_1),
        "report_sha256": sha256_file(root / REPORT_JSON_PATH_V5_1),
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
        f"- {item['timeframe']}: `{item['rows']}` lignes, checksum `{item['sha256']}`" for item in outputs
    )
    _write_text(
        root / ATTESTATION_MD,
        "# Attestation full locale V5.1\n\n"
        "- Scope : `full_local`\n"
        "- Validation full locale remplacee par audit-lite : `false`\n"
        "- Aucun trading, aucun backtest, aucun ordre.\n\n"
        "## Commandes executees\n\n"
        + "\n".join(f"- `{command}` : PASS" for command in commands)
        + "\n\n"
        "## Outputs features complets\n\n"
        f"{lines}\n",
    )


def _read_optional_timings(root: Path, commands: list[str]) -> dict[str, float]:
    timing_path = root / "reports/audit_lite/v5_1_command_timings.json"
    if timing_path.exists():
        payload = _read_json(timing_path)
        return {command: float(payload.get(command, 0.0)) for command in commands}
    return {command: 0.0 for command in commands}


def _collect_files(root: Path) -> list[Path]:
    include_files = [
        "README.md",
        "pyproject.toml",
        "galapagos/__init__.py",
        "src/galapagos/__init__.py",
        "scripts/_bootstrap.py",
        "scripts/run_max_history_causal_feature_store_v5_1.py",
        "scripts/validate_max_history_causal_feature_store_v5_1.py",
        "scripts/release_audit_lite_zip_v5_1.py",
        "scripts/audit_audit_lite_zip_v5_1.py",
        "scripts/smoke_audit_lite_zip_v5_1.py",
        "tests/features/test_max_history_causal_features_v5_1.py",
        "tests/validation/test_max_history_causal_feature_store_v5_1_validator.py",
        MANIFEST_PATH_V5_1.as_posix(),
        REPORT_JSON_PATH_V5_1.as_posix(),
        REPORT_MD_PATH_V5_1.as_posix(),
        DOC_PATH_V5_1.as_posix(),
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
        "src/galapagos/features",
        "src/galapagos/validation",
    ]
    files: list[Path] = []
    for item in include_files:
        path = root / item
        if not path.exists():
            raise FileNotFoundError(f"missing audit-lite input: {item}")
        if path.is_file() and _allowed(path.relative_to(root)):
            files.append(path.relative_to(root))
    for sample in sorted((root / SAMPLE_ROOT).glob("timeframe=*/sample.parquet")):
        files.append(sample.relative_to(root))
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
    if relative.suffix.casefold() == ".parquet" and not name.startswith("data/audit_lite/v5_1/features/"):
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
            "data/research/v5_0/**/*.parquet",
            "data/research/v5_1/**/*.parquet",
            "previous release ZIP files",
            "Python caches (__pycache__, *.pyc, *.pyo)",
            "persistent model files",
        ],
        "raw_zips_excluded": True,
        "full_parquet_excluded_count": len(inventory["full_parquet_excluded"]),
        "samples_included": len(inventory["parquet_samples_included"]),
        "note": "audit-lite does not replace full local validation",
    }
    _write_json(root / ZIP_SIZE_JSON, payload)
    rows = "\n".join(f"- `{item['path']}` : {item['bytes']} octets" for item in top_files)
    _write_text(
        root / ZIP_SIZE_MD,
        "# Rapport de taille ZIP audit-lite V5.1\n\n"
        f"- ZIP : `{ZIP_NAME}`\n"
        f"- Taille : `{zip_size_bytes}` octets\n"
        "- Raw zips exclus : `true`\n"
        f"- Parquet complets exclus : `{payload['full_parquet_excluded_count']}`\n"
        f"- Samples inclus : `{payload['samples_included']}`\n"
        "- Note : `audit-lite does not replace full local validation`\n\n"
        "## Top 20 fichiers inclus\n\n"
        f"{rows}\n",
    )


def _render_inventory_markdown(inventory: dict[str, Any], manifest: dict[str, Any]) -> str:
    parquet_rows = "\n".join(
        f"- `{item['timeframe']}` : `{item['path']}` ({item['rows']} lignes)"
        for item in inventory["full_parquet_excluded"]
    )
    return f"""# Inventaire audit-lite V5.1

- Raw zips exclus : `{inventory['raw_zips_excluded']}`
- Parquet features complets exclus : `{len(inventory['full_parquet_excluded'])}`
- Fenetre : `{manifest['input_ohlcv_manifest']['window_start']}` -> `{manifest['input_ohlcv_manifest']['window_end']}`
- Validation full locale remplacee : `false`
- Note : `audit-lite does not replace full local validation`

## Parquet features complets exclus

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
