from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

import _bootstrap

_bootstrap.bootstrap_src_path()

import pandas as pd

from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet, write_parquet
from galapagos.features.schemas import FEATURE_COLUMNS_V3_6


VERSION = "V3.6"
ZIP_NAME = "projet-galapagos-v3.6-audit-lite.zip"
AUDIT_LITE_DIR = Path("reports/audit_lite")
ARTIFACT_INVENTORY_JSON = AUDIT_LITE_DIR / "v3_6_artifact_inventory.json"
ARTIFACT_INVENTORY_MD = AUDIT_LITE_DIR / "v3_6_artifact_inventory.md"
PARQUET_SUMMARY_JSON = AUDIT_LITE_DIR / "v3_6_parquet_summary.json"
ZIP_SIZE_JSON = AUDIT_LITE_DIR / "zip_size_report_v3_6.json"
ZIP_SIZE_MD = AUDIT_LITE_DIR / "zip_size_report_v3_6.md"
FULL_LOCAL_ATTESTATION_JSON = AUDIT_LITE_DIR / "v3_6_full_local_validation_attestation.json"
FULL_LOCAL_ATTESTATION_MD = AUDIT_LITE_DIR / "v3_6_full_local_validation_attestation.md"
V3_5_MANIFEST = Path("reports/manifests/expanded_public_market_data_v3_5_manifest.json")
V3_6_MANIFEST = Path("reports/manifests/expanded_causal_feature_store_v3_6_manifest.json")
V3_6_REPORT = Path("reports/features/expanded_causal_feature_store_v3_6.json")
TIMEFRAMES = ["1m", "5m", "15m", "1h"]
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
]
FORBIDDEN_SUFFIXES = {".pkl", ".pickle", ".joblib", ".ckpt", ".pt", ".pth", ".onnx"}
FORBIDDEN_FEATURE_COLUMNS = {
    "future_return",
    "label",
    "target",
    "prediction",
    "signal",
    "strategy",
    "order",
    "pnl",
    "backtest",
}


def main() -> None:
    root = Path(".").resolve()
    AUDIT_LITE_DIR.mkdir(parents=True, exist_ok=True)
    manifest_v3_5 = _read_json(root / V3_5_MANIFEST)
    manifest_v3_6 = _read_json(root / V3_6_MANIFEST)
    report_v3_6 = _read_json(root / V3_6_REPORT)
    if manifest_v3_6 != report_v3_6:
        raise RuntimeError("V3.6 manifest and report must match before audit-lite release.")

    raw_inventory = _build_raw_inventory(manifest_v3_5)
    parquet_summary, samples = _build_parquet_summary_and_samples(root, manifest_v3_6)
    full_parquet_excluded = _build_full_parquet_exclusions(root, manifest_v3_5, manifest_v3_6)
    artifact_inventory = {
        "version": VERSION,
        "audit_lite_does_not_replace_full_validation": True,
        "raw_zips_excluded": raw_inventory,
        "full_parquet_excluded": full_parquet_excluded,
        "sample_parquets_included": samples,
        "notes": [
            "audit-lite does not replace full local validation",
            "Production validators still require full local raw zips and production Parquet outputs.",
            "Raw Binance zip files are represented by inventory metadata only.",
        ],
    }
    _write_json(root / ARTIFACT_INVENTORY_JSON, artifact_inventory)
    _write_json(root / PARQUET_SUMMARY_JSON, parquet_summary)
    _write_text(root / ARTIFACT_INVENTORY_MD, _render_inventory_markdown(artifact_inventory))
    _write_json(
        root / ZIP_SIZE_JSON,
        {
            "version": VERSION,
            "zip_name": ZIP_NAME,
            "zip_size_bytes": 0,
            "top_20_largest_files_included": [],
            "heavy_files_excluded": [],
            "raw_zips_excluded": True,
            "raw_zips_represented_in_inventory": len(raw_inventory),
            "full_parquet_excluded_count": len(full_parquet_excluded),
            "sample_parquet_count": len(samples),
            "note": "audit-lite does not replace full local validation",
        },
    )
    _write_text(
        root / ZIP_SIZE_MD,
        "# Rapport de taille ZIP audit-lite V3.6\n\n"
        "- Note : `audit-lite does not replace full local validation`\n",
    )

    zip_path = root / ZIP_NAME
    zip_size_bytes = 0
    included = _collect_audit_lite_files(root)
    for _attempt in range(5):
        _write_size_report(root, zip_size_bytes=zip_size_bytes, included=included, artifact_inventory=artifact_inventory)
        included = _collect_audit_lite_files(root)
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
        "raw_zip_inventory_count": len(raw_inventory),
        "full_parquet_excluded_count": len(full_parquet_excluded),
        "sample_parquet_count": len(samples),
        "audit_lite_does_not_replace_full_validation": True,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _build_raw_inventory(manifest_v3_5: dict[str, Any]) -> list[dict[str, Any]]:
    source = manifest_v3_5["source"]
    inventory: list[dict[str, Any]] = []
    for current_date, payload in sorted(manifest_v3_5["raw_files"].items()):
        inventory.append(
            {
                "date": current_date,
                "path": payload["path"],
                "sha256": payload["sha256"],
                "bytes": int(payload["bytes"]),
                "rows": int(payload["rows"]),
                "source": source["name"],
                "symbol": source["symbol"],
                "timeframe": source["source_timeframe"],
            }
        )
    return inventory


def _build_parquet_summary_and_samples(
    root: Path,
    manifest_v3_6: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    summaries: dict[str, dict[str, Any]] = {}
    samples: list[dict[str, Any]] = []
    for timeframe in TIMEFRAMES:
        output = manifest_v3_6["outputs"][timeframe]
        full_path = root / output["path"]
        frame = read_parquet(full_path)
        schema_strict = list(frame.columns) == FEATURE_COLUMNS_V3_6
        summary = {
            "path": output["path"],
            "sha256": sha256_file(full_path),
            "bytes": full_path.stat().st_size,
            "rows": int(len(frame)),
            "columns": list(frame.columns),
            "min_event_ts": _ts_iso(frame["event_ts"].min()),
            "max_event_ts": _ts_iso(frame["event_ts"].max()),
            "null_counts_by_column": {column: int(value) for column, value in frame.isna().sum().items()},
            "forbidden_columns_present": _find_forbidden_columns(frame.columns),
            "source_ohlcv_sha256_distinct": sorted(frame["source_ohlcv_sha256"].astype(str).unique().tolist()),
            "schema_strict": schema_strict,
        }
        summaries[timeframe] = summary
        sample = _sample_feature_frame(frame)
        if list(sample.columns) != FEATURE_COLUMNS_V3_6:
            raise RuntimeError(f"V3.6 audit-lite sample schema mismatch for {timeframe}")
        sample_path = root / "data/audit_lite/v3_6/features" / f"timeframe={timeframe}" / "sample.parquet"
        write_parquet(sample[FEATURE_COLUMNS_V3_6], sample_path)
        samples.append(
            {
                "timeframe": timeframe,
                "path": str(sample_path.relative_to(root)),
                "sha256": sha256_file(sample_path),
                "bytes": sample_path.stat().st_size,
                "rows": int(len(sample)),
                "source_full_path": output["path"],
                "source_full_sha256": output["sha256"],
            }
        )
    return {
        "version": VERSION,
        "audit_lite_does_not_replace_full_validation": True,
        "feature_schema": "FEATURE_COLUMNS_V3_6",
        "features": summaries,
    }, samples


def _build_full_parquet_exclusions(
    root: Path,
    manifest_v3_5: dict[str, Any],
    manifest_v3_6: dict[str, Any],
) -> list[dict[str, Any]]:
    excluded: list[dict[str, Any]] = []
    for timeframe, payload in sorted(manifest_v3_5["outputs"].items()):
        path = root / payload["path"]
        columns = _read_columns(path)
        excluded.append(
            {
                "timeframe": timeframe,
                "path": payload["path"],
                "sha256": payload["sha256"],
                "bytes": int(payload["bytes"]),
                "rows": int(payload["rows"]),
                "columns": columns,
                "schema_version": "OHLCV_COLUMNS",
                "reason_excluded": "full V3.5 OHLCV Parquet is represented by manifest metadata in audit-lite",
            }
        )
    for timeframe, payload in sorted(manifest_v3_6["outputs"].items()):
        path = root / payload["path"]
        columns = _read_columns(path)
        excluded.append(
            {
                "timeframe": timeframe,
                "path": payload["path"],
                "sha256": payload["sha256"],
                "bytes": int(payload["bytes"]),
                "rows": int(payload["rows"]),
                "columns": columns,
                "schema_version": manifest_v3_6["feature_schema_version"],
                "reason_excluded": "full V3.6 feature Parquet is replaced by deterministic schema-preserving samples in audit-lite",
            }
        )
    return excluded


def _sample_feature_frame(frame: pd.DataFrame) -> pd.DataFrame:
    row_count = len(frame)
    indexes: set[int] = set()
    indexes.update(range(min(100, row_count)))
    indexes.update(range(max(0, row_count - 100), row_count))
    indexes.update(range(max(0, 30 - 20), min(row_count, 30 + 21)))
    middle = row_count // 2
    indexes.update(range(max(0, middle - 50), min(row_count, middle + 50)))
    if row_count:
        step = max(1, row_count // 100)
        indexes.update(range(0, row_count, step))
    return frame.iloc[sorted(index for index in indexes if 0 <= index < row_count)].reset_index(drop=True)


def _collect_audit_lite_files(root: Path) -> list[Path]:
    include_files = [
        "README.md",
        "pyproject.toml",
        "galapagos/__init__.py",
        "scripts/_bootstrap.py",
        "scripts/run_expanded_public_market_data_v3_5.py",
        "scripts/validate_expanded_public_market_data_v3_5.py",
        "scripts/run_expanded_causal_feature_store_v3_6.py",
        "scripts/validate_expanded_causal_feature_store_v3_6.py",
        "scripts/release_clean_zip_v3_6.py",
        "scripts/audit_clean_zip_v3_6.py",
        "scripts/smoke_test_clean_zip_v3_6.py",
        "scripts/release_audit_lite_zip_v3_6.py",
        "scripts/audit_audit_lite_zip_v3_6.py",
        "scripts/smoke_audit_lite_zip_v3_6.py",
        "tests/features/test_expanded_causal_features_v3_6.py",
        "tests/validation/test_expanded_causal_feature_store_v3_6_validator.py",
        "reports/manifests/expanded_public_market_data_v3_5_manifest.json",
        "reports/manifests/expanded_causal_feature_store_v3_6_manifest.json",
        "reports/data_quality/expanded_public_market_data_v3_5.json",
        "reports/data_quality/expanded_public_market_data_v3_5.md",
        "reports/features/expanded_causal_feature_store_v3_6.json",
        "reports/features/expanded_causal_feature_store_v3_6.md",
        "reports/PROJECT_STATE.json",
        "reports/PROJECT_STATE.md",
        "reports/current/latest_metrics.json",
        "reports/current/latest_metrics.md",
        "reports/current/latest_summary.md",
        "docs/expanded_public_market_data_v3_5.md",
        "docs/expanded_causal_feature_store_v3_6.md",
        str(ARTIFACT_INVENTORY_JSON),
        str(ARTIFACT_INVENTORY_MD),
        str(PARQUET_SUMMARY_JSON),
        str(ZIP_SIZE_JSON),
        str(ZIP_SIZE_MD),
    ]
    optional_files = [
        str(FULL_LOCAL_ATTESTATION_JSON),
        str(FULL_LOCAL_ATTESTATION_MD),
    ]
    include_dirs = [
        "src/galapagos/data/public_market",
        "src/galapagos/validation",
        "src/galapagos/features",
        "src/galapagos/labels",
        "src/galapagos/datasets",
        "src/galapagos/ml",
        "data/audit_lite/v3_6/features",
    ]
    files: list[Path] = []
    for item in include_files:
        path = root / item
        if not path.exists():
            raise FileNotFoundError(f"missing audit-lite input: {item}")
        if path.is_file() and _allowed(path.relative_to(root)):
            files.append(path.relative_to(root))
    for item in optional_files:
        path = root / item
        if path.exists() and path.is_file() and _allowed(path.relative_to(root)):
            files.append(path.relative_to(root))
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
    if any(part in FORBIDDEN_PARTS for part in relative.parts):
        return False
    if relative.name in {".DS_Store", ".env"} or relative.name.startswith(".smoke-"):
        return False
    if "secret" in name.casefold():
        return False
    if relative.suffix.casefold() in FORBIDDEN_SUFFIXES:
        return False
    if relative.suffix.casefold() == ".zip":
        return False
    if name.endswith(".parquet") and not name.startswith("data/audit_lite/v3_6/features/"):
        return False
    return not any(name.startswith(prefix) for prefix in FORBIDDEN_PREFIXES)


def _write_zip(root: Path, zip_path: Path, included: list[Path]) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in included:
            archive.write(root / relative, relative.as_posix())


def _write_size_report(
    root: Path,
    *,
    zip_size_bytes: int,
    included: list[Path],
    artifact_inventory: dict[str, Any],
) -> None:
    top_files = sorted(
        (
            {
                "path": path.as_posix(),
                "bytes": (root / path).stat().st_size,
            }
            for path in included
        ),
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
            "data/research/v3_5/silver/**/*.parquet",
            "data/research/v3_6/features/**/*.parquet",
            "previous release ZIP files",
        ],
        "raw_zips_excluded": True,
        "raw_zips_represented_in_inventory": len(artifact_inventory["raw_zips_excluded"]),
        "full_parquet_excluded_count": len(artifact_inventory["full_parquet_excluded"]),
        "sample_parquet_count": len(artifact_inventory["sample_parquets_included"]),
        "note": "audit-lite does not replace full local validation",
    }
    _write_json(root / ZIP_SIZE_JSON, payload)
    rows = "\n".join(f"- `{item['path']}` : {item['bytes']} octets" for item in top_files)
    _write_text(
        root / ZIP_SIZE_MD,
        "# Rapport de taille ZIP audit-lite V3.6\n\n"
        f"- ZIP : `{ZIP_NAME}`\n"
        f"- Taille : `{zip_size_bytes}` octets\n"
        "- Raw zips exclus : `true`\n"
        f"- Raw zips representes dans l'inventaire : `{payload['raw_zips_represented_in_inventory']}`\n"
        f"- Parquet complets exclus : `{payload['full_parquet_excluded_count']}`\n"
        f"- Samples Parquet inclus : `{payload['sample_parquet_count']}`\n"
        "- Note : `audit-lite does not replace full local validation`\n\n"
        "## Top 20 fichiers inclus\n\n"
        f"{rows}\n",
    )


def _render_inventory_markdown(inventory: dict[str, Any]) -> str:
    raw_count = len(inventory["raw_zips_excluded"])
    parquet_count = len(inventory["full_parquet_excluded"])
    sample_rows = "\n".join(
        f"- `{item['timeframe']}` : `{item['path']}` ({item['rows']} lignes)"
        for item in inventory["sample_parquets_included"]
    )
    return f"""# Inventaire audit-lite V3.6

Ce rapport decrit les artefacts lourds exclus du ZIP `audit-lite`.

- Raw zips exclus : `{raw_count}`
- Parquet complets exclus : `{parquet_count}`
- Validation full locale remplacee : `false`
- Note : `audit-lite does not replace full local validation`

## Samples Parquet inclus

{sample_rows}

## Garantie de scope

Les validateurs de production ne sont pas relaches. Le ZIP audit-lite sert a transmettre le code, les rapports, les manifests, les checksums et des samples stricts. Il ne pretend pas revalider physiquement les 90 jours sans les raw zips locaux.
"""


def _find_forbidden_columns(columns: pd.Index) -> list[str]:
    found: list[str] = []
    for column in columns:
        folded = str(column).casefold()
        if any(term in folded for term in FORBIDDEN_FEATURE_COLUMNS):
            found.append(str(column))
    return found


def _read_columns(path: Path) -> list[str]:
    return [str(column) for column in read_parquet(path).columns]


def _ts_iso(value: Any) -> str:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    return timestamp.isoformat().replace("+00:00", "Z")


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
