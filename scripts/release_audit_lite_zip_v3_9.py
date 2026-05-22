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
from galapagos.ml.schemas import (
    FORBIDDEN_OUTPUT_TERMS_V3_9,
    ML_SCORE_COLUMNS_V3_9,
    TIMEFRAMES_V3_9,
)


VERSION = "V3.9"
ZIP_NAME = "projet-galapagos-v3.9-audit-lite.zip"
AUDIT_LITE_DIR = Path("reports/audit_lite")
ARTIFACT_INVENTORY_JSON = AUDIT_LITE_DIR / "v3_9_artifact_inventory.json"
ARTIFACT_INVENTORY_MD = AUDIT_LITE_DIR / "v3_9_artifact_inventory.md"
PARQUET_SUMMARY_JSON = AUDIT_LITE_DIR / "v3_9_parquet_summary.json"
ZIP_SIZE_JSON = AUDIT_LITE_DIR / "zip_size_report_v3_9.json"
ZIP_SIZE_MD = AUDIT_LITE_DIR / "zip_size_report_v3_9.md"
FULL_LOCAL_ATTESTATION_JSON = AUDIT_LITE_DIR / "v3_9_full_local_validation_attestation.json"
FULL_LOCAL_ATTESTATION_MD = AUDIT_LITE_DIR / "v3_9_full_local_validation_attestation.md"
V3_5_MANIFEST = Path("reports/manifests/expanded_public_market_data_v3_5_manifest.json")
V3_8_MANIFEST = Path("reports/manifests/expanded_offline_supervised_dataset_v3_8_manifest.json")
V3_9_MANIFEST = Path("reports/manifests/expanded_offline_ml_research_v3_9_manifest.json")
V3_9_REPORT = Path("reports/ml/expanded_offline_ml_research_v3_9.json")
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
    "data/research/v3_9/backtests/",
    "data/research/v3_9/strategies/",
]
FORBIDDEN_SUFFIXES = {".pkl", ".pickle", ".joblib", ".ckpt", ".pt", ".pth", ".onnx"}


def main() -> None:
    root = Path(".").resolve()
    AUDIT_LITE_DIR.mkdir(parents=True, exist_ok=True)
    manifest_v3_5 = _read_json(root / V3_5_MANIFEST)
    manifest_v3_8 = _read_json(root / V3_8_MANIFEST)
    manifest_v3_9 = _read_json(root / V3_9_MANIFEST)
    report_v3_9 = _read_json(root / V3_9_REPORT)
    if manifest_v3_9 != report_v3_9:
        raise RuntimeError("V3.9 manifest and report must match before audit-lite release.")

    raw_inventory = _build_raw_inventory(manifest_v3_5)
    parquet_summary, samples = _build_parquet_summary_and_samples(root, manifest_v3_9)
    full_parquet_excluded = _build_full_parquet_exclusions(root, manifest_v3_8, manifest_v3_9)
    artifact_inventory = {
        "version": VERSION,
        "audit_lite_does_not_replace_full_validation": True,
        "raw_zips_excluded": raw_inventory,
        "full_parquet_excluded": full_parquet_excluded,
        "sample_parquets_included": samples,
        "notes": [
            "audit-lite does not replace full local validation",
            "Production validators still require full local V3.8 datasets and V3.9 score outputs.",
            "V3.9 scores are offline research baselines and are not trading signals.",
        ],
    }
    _write_json(root / ARTIFACT_INVENTORY_JSON, artifact_inventory)
    _write_json(root / PARQUET_SUMMARY_JSON, parquet_summary)
    _write_text(root / ARTIFACT_INVENTORY_MD, _render_inventory_markdown(artifact_inventory))
    _write_json(root / ZIP_SIZE_JSON, _empty_size_payload(raw_inventory, full_parquet_excluded, samples))
    _write_text(root / ZIP_SIZE_MD, "# Rapport de taille ZIP audit-lite V3.9\n\n- Note : `audit-lite does not replace full local validation`\n")

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
    return [
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
        for current_date, payload in sorted(manifest_v3_5["raw_files"].items())
    ]


def _build_parquet_summary_and_samples(root: Path, manifest_v3_9: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    score_summaries: dict[str, dict[str, Any]] = {}
    samples: list[dict[str, Any]] = []
    for timeframe in TIMEFRAMES_V3_9:
        output = manifest_v3_9["outputs"][timeframe]
        score_path = root / output["path"]
        scores = read_parquet(score_path)
        score_summaries[timeframe] = _parquet_summary(root, score_path, scores)
        sample = _sample_frame(scores)
        if list(sample.columns) != ML_SCORE_COLUMNS_V3_9:
            raise RuntimeError(f"V3.9 audit-lite score sample schema mismatch for {timeframe}")
        sample_path = root / "data/audit_lite/v3_9/ml_scores" / f"timeframe={timeframe}" / "sample.parquet"
        write_parquet(sample[ML_SCORE_COLUMNS_V3_9], sample_path)
        samples.append(_sample_block(root, sample_path, sample, output["path"], output["sha256"], timeframe))
    return (
        {
            "version": VERSION,
            "audit_lite_does_not_replace_full_validation": True,
            "score_schema": "ML_SCORE_COLUMNS_V3_9",
            "scores": score_summaries,
        },
        samples,
    )


def _parquet_summary(root: Path, path: Path, frame: pd.DataFrame) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(root)),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "rows": int(len(frame)),
        "columns": list(frame.columns),
        "min_event_ts": _ts_iso(frame["event_ts"].min()) if len(frame) else None,
        "max_event_ts": _ts_iso(frame["event_ts"].max()) if len(frame) else None,
        "null_counts_by_column": {column: int(value) for column, value in frame.isna().sum().items()},
        "forbidden_columns_present": _find_forbidden_columns(frame.columns),
        "dataset_sha256_distinct": sorted(frame["dataset_sha256"].astype(str).unique().tolist()) if "dataset_sha256" in frame.columns else [],
        "model_names": sorted(frame["model_name"].astype(str).unique().tolist()) if "model_name" in frame.columns else [],
        "target_names": sorted(frame["target_name"].astype(str).unique().tolist()) if "target_name" in frame.columns else [],
        "schema_strict": list(frame.columns) == ML_SCORE_COLUMNS_V3_9,
    }


def _sample_frame(frame: pd.DataFrame) -> pd.DataFrame:
    row_count = len(frame)
    indexes: set[int] = set()
    indexes.update(range(min(100, row_count)))
    indexes.update(range(max(0, row_count - 120), row_count))
    middle = row_count // 2
    indexes.update(range(max(0, middle - 50), min(row_count, middle + 50)))
    if row_count:
        step = max(1, row_count // 100)
        indexes.update(range(0, row_count, step))
    return frame.iloc[sorted(index for index in indexes if 0 <= index < row_count)].reset_index(drop=True)


def _sample_block(root: Path, path: Path, frame: pd.DataFrame, source_full_path: str, source_full_sha256: str, timeframe: str) -> dict[str, Any]:
    return {
        "timeframe": timeframe,
        "artifact_type": "ml_scores",
        "path": str(path.relative_to(root)),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "rows": int(len(frame)),
        "source_full_path": source_full_path,
        "source_full_sha256": source_full_sha256,
    }


def _build_full_parquet_exclusions(root: Path, manifest_v3_8: dict[str, Any], manifest_v3_9: dict[str, Any]) -> list[dict[str, Any]]:
    excluded: list[dict[str, Any]] = []
    for layer, manifest, section, schema in [
        ("V3.8 datasets", manifest_v3_8, "outputs", "DATASET_COLUMNS_V3_8"),
        ("V3.8 splits", manifest_v3_8, "splits", "SPLIT_COLUMNS_V3_8"),
        ("V3.9 ML research scores", manifest_v3_9, "outputs", "ML_SCORE_COLUMNS_V3_9"),
    ]:
        for timeframe, payload in sorted(manifest[section].items()):
            path = root / payload["path"]
            excluded.append(
                {
                    "layer": layer,
                    "timeframe": timeframe,
                    "path": payload["path"],
                    "sha256": payload["sha256"],
                    "bytes": int(payload.get("bytes", path.stat().st_size)),
                    "rows": int(payload["rows"]),
                    "columns": _read_columns(path),
                    "schema_version": schema,
                    "reason_excluded": f"full {layer} Parquet is represented by manifest metadata and deterministic samples in audit-lite",
                }
            )
    return excluded


def _collect_audit_lite_files(root: Path) -> list[Path]:
    include_files = [
        "README.md",
        "pyproject.toml",
        "galapagos/__init__.py",
        "scripts/_bootstrap.py",
        "scripts/run_expanded_offline_supervised_dataset_v3_8.py",
        "scripts/validate_expanded_offline_supervised_dataset_v3_8.py",
        "scripts/run_expanded_offline_ml_research_v3_9.py",
        "scripts/validate_expanded_offline_ml_research_v3_9.py",
        "scripts/release_audit_lite_zip_v3_9.py",
        "scripts/audit_audit_lite_zip_v3_9.py",
        "scripts/smoke_audit_lite_zip_v3_9.py",
        "tests/ml/test_expanded_offline_ml_research_v3_9.py",
        "tests/validation/test_expanded_offline_ml_research_v3_9_validator.py",
        "reports/manifests/expanded_public_market_data_v3_5_manifest.json",
        "reports/manifests/expanded_offline_supervised_dataset_v3_8_manifest.json",
        "reports/manifests/expanded_offline_ml_research_v3_9_manifest.json",
        "reports/datasets/expanded_offline_supervised_dataset_v3_8.json",
        "reports/ml/expanded_offline_ml_research_v3_9.json",
        "reports/ml/expanded_offline_ml_research_v3_9.md",
        "reports/ml/expanded_offline_research_scores_v3_9.json",
        "reports/ml/expanded_offline_research_scores_v3_9.md",
        "reports/PROJECT_STATE.json",
        "reports/PROJECT_STATE.md",
        "reports/current/latest_metrics.json",
        "reports/current/latest_metrics.md",
        "reports/current/latest_summary.md",
        "docs/expanded_offline_ml_research_v3_9.md",
        str(ARTIFACT_INVENTORY_JSON),
        str(ARTIFACT_INVENTORY_MD),
        str(PARQUET_SUMMARY_JSON),
        str(ZIP_SIZE_JSON),
        str(ZIP_SIZE_MD),
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
        "data/audit_lite/v3_9/ml_scores",
    ]
    files: list[Path] = []
    for item in include_files:
        path = root / item
        if not path.exists():
            raise FileNotFoundError(f"missing audit-lite input: {item}")
        if path.is_file() and _allowed(path.relative_to(root)):
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
    if relative.suffix.casefold() == ".parquet" and not name.startswith("data/audit_lite/v3_9/ml_scores/"):
        return False
    return not any(name.startswith(prefix) for prefix in FORBIDDEN_PREFIXES)


def _write_size_report(root: Path, *, zip_size_bytes: int, included: list[Path], artifact_inventory: dict[str, Any]) -> None:
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
            "data/research/v3_8/datasets/**/*.parquet",
            "data/research/v3_9/ml/**/*.parquet",
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
        "# Rapport de taille ZIP audit-lite V3.9\n\n"
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


def _empty_size_payload(raw_inventory: list[dict[str, Any]], excluded: list[dict[str, Any]], samples: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "zip_name": ZIP_NAME,
        "zip_size_bytes": 0,
        "top_20_largest_files_included": [],
        "heavy_files_excluded": [],
        "raw_zips_excluded": True,
        "raw_zips_represented_in_inventory": len(raw_inventory),
        "full_parquet_excluded_count": len(excluded),
        "sample_parquet_count": len(samples),
        "note": "audit-lite does not replace full local validation",
    }


def _render_inventory_markdown(inventory: dict[str, Any]) -> str:
    sample_rows = "\n".join(
        f"- `{item['timeframe']}` `{item['artifact_type']}` : `{item['path']}` ({item['rows']} lignes)"
        for item in inventory["sample_parquets_included"]
    )
    return f"""# Inventaire audit-lite V3.9

Ce rapport decrit les artefacts lourds exclus du ZIP `audit-lite`.

- Raw zips exclus : `{len(inventory['raw_zips_excluded'])}`
- Parquet complets exclus : `{len(inventory['full_parquet_excluded'])}`
- Validation full locale remplacee : `false`
- Note : `audit-lite does not replace full local validation`

## Samples Parquet scores inclus

{sample_rows}

## Garantie de scope

Les validateurs de production ne sont pas relaches. Le ZIP audit-lite sert a transmettre le code, les rapports, les manifests, les checksums et des samples stricts. Il ne pretend pas revalider physiquement les 90 jours sans les donnees completes locales.
"""


def _write_zip(root: Path, zip_path: Path, included: list[Path]) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in included:
            archive.write(root / relative, relative.as_posix())


def _find_forbidden_columns(columns: pd.Index) -> list[str]:
    return sorted(str(column) for column in columns if any(term in str(column).casefold() for term in FORBIDDEN_OUTPUT_TERMS_V3_9))


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
