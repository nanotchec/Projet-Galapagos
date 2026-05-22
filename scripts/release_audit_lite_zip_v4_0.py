from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.data.public_market.provenance import sha256_file


VERSION = "V4.0"
ZIP_NAME = "projet-galapagos-v4.0-audit-lite.zip"
AUDIT_LITE_DIR = Path("reports/audit_lite")
ARTIFACT_INVENTORY_JSON = AUDIT_LITE_DIR / "v4_0_artifact_inventory.json"
ARTIFACT_INVENTORY_MD = AUDIT_LITE_DIR / "v4_0_artifact_inventory.md"
ZIP_SIZE_JSON = AUDIT_LITE_DIR / "zip_size_report_v4_0.json"
ZIP_SIZE_MD = AUDIT_LITE_DIR / "zip_size_report_v4_0.md"
FULL_LOCAL_ATTESTATION_JSON = AUDIT_LITE_DIR / "v4_0_full_local_validation_attestation.json"
FULL_LOCAL_ATTESTATION_MD = AUDIT_LITE_DIR / "v4_0_full_local_validation_attestation.md"
V4_0_MANIFEST = Path("reports/manifests/expanded_ml_robustness_v4_0_manifest.json")
V4_0_REPORT = Path("reports/ml/expanded_ml_robustness_v4_0.json")
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
FORBIDDEN_SUFFIXES = {".pkl", ".pickle", ".joblib", ".ckpt", ".pt", ".pth", ".onnx"}


def main() -> None:
    root = Path(".").resolve()
    AUDIT_LITE_DIR.mkdir(parents=True, exist_ok=True)
    manifest = _read_json(root / V4_0_MANIFEST)
    report = _read_json(root / V4_0_REPORT)
    if manifest != report:
        raise RuntimeError("V4.0 manifest and report must match before audit-lite release.")

    inventory = _build_artifact_inventory(root, manifest)
    _write_json(root / ARTIFACT_INVENTORY_JSON, inventory)
    _write_text(root / ARTIFACT_INVENTORY_MD, _render_inventory_markdown(inventory))
    _write_json(root / ZIP_SIZE_JSON, _empty_size_payload(inventory))
    _write_text(root / ZIP_SIZE_MD, "# Rapport de taille ZIP audit-lite V4.0\n\n- Note : `audit-lite does not replace full local validation`\n")

    zip_path = root / ZIP_NAME
    zip_size_bytes = 0
    included = _collect_audit_lite_files(root)
    for _attempt in range(5):
        _write_size_report(root, zip_size_bytes=zip_size_bytes, included=included, inventory=inventory)
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
        "full_parquet_excluded_count": len(inventory["full_parquet_excluded"]),
        "audit_lite_does_not_replace_full_validation": True,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _build_artifact_inventory(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    score_files = [
        {
            "timeframe": timeframe,
            "path": payload["path"],
            "sha256": payload["sha256"],
            "rows": int(payload["rows"]),
            "reason_excluded": "full V3.9 score Parquet is represented by V4.0 checksums and reports in audit-lite",
        }
        for timeframe, payload in sorted(manifest["input_score_files"].items())
    ]
    input_manifests = [
        {
            "path": manifest["input_dataset_manifest"]["path"],
            "sha256": manifest["input_dataset_manifest"]["sha256"],
        },
        {
            "path": manifest["input_ml_manifest"]["path"],
            "sha256": manifest["input_ml_manifest"]["sha256"],
        },
    ]
    return {
        "version": VERSION,
        "audit_lite_does_not_replace_full_validation": True,
        "raw_zips_excluded": True,
        "input_manifests": input_manifests,
        "full_parquet_excluded": score_files,
        "included_reports": [
            {"path": V4_0_MANIFEST.as_posix(), "sha256": sha256_file(root / V4_0_MANIFEST)},
            {"path": V4_0_REPORT.as_posix(), "sha256": sha256_file(root / V4_0_REPORT)},
        ],
        "notes": [
            "audit-lite does not replace full local validation",
            "V4.0 contains no raw zips, full Parquet data, backtest, strategy, order, execution artifact, or persistent model.",
        ],
    }


def _collect_audit_lite_files(root: Path) -> list[Path]:
    include_files = [
        "README.md",
        "pyproject.toml",
        "galapagos/__init__.py",
        "scripts/_bootstrap.py",
        "scripts/run_expanded_ml_robustness_v4_0.py",
        "scripts/validate_expanded_ml_robustness_v4_0.py",
        "scripts/release_audit_lite_zip_v4_0.py",
        "scripts/audit_audit_lite_zip_v4_0.py",
        "scripts/smoke_audit_lite_zip_v4_0.py",
        "tests/ml/test_expanded_ml_robustness_v4_0.py",
        "tests/validation/test_expanded_ml_robustness_v4_0_validator.py",
        "reports/manifests/expanded_ml_robustness_v4_0_manifest.json",
        "reports/ml/expanded_ml_robustness_v4_0.json",
        "reports/ml/expanded_ml_robustness_v4_0.md",
        "reports/PROJECT_STATE.json",
        "reports/PROJECT_STATE.md",
        "reports/current/latest_metrics.json",
        "reports/current/latest_metrics.md",
        "reports/current/latest_summary.md",
        "docs/expanded_ml_robustness_v4_0.md",
        str(ARTIFACT_INVENTORY_JSON),
        str(ARTIFACT_INVENTORY_MD),
        str(ZIP_SIZE_JSON),
        str(ZIP_SIZE_MD),
        str(FULL_LOCAL_ATTESTATION_JSON),
        str(FULL_LOCAL_ATTESTATION_MD),
    ]
    include_dirs = [
        "src/galapagos/data/public_market",
        "src/galapagos/validation",
        "src/galapagos/datasets",
        "src/galapagos/ml",
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
    if relative.suffix.casefold() in {".zip", ".parquet"}:
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
            "data/research/**/*.parquet",
            "previous release ZIP files",
            "persistent model files",
        ],
        "raw_zips_excluded": True,
        "full_parquet_excluded_count": len(inventory["full_parquet_excluded"]),
        "note": "audit-lite does not replace full local validation",
    }
    _write_json(root / ZIP_SIZE_JSON, payload)
    rows = "\n".join(f"- `{item['path']}` : {item['bytes']} octets" for item in top_files)
    _write_text(
        root / ZIP_SIZE_MD,
        "# Rapport de taille ZIP audit-lite V4.0\n\n"
        f"- ZIP : `{ZIP_NAME}`\n"
        f"- Taille : `{zip_size_bytes}` octets\n"
        "- Raw zips exclus : `true`\n"
        f"- Parquet complets exclus : `{payload['full_parquet_excluded_count']}`\n"
        "- Note : `audit-lite does not replace full local validation`\n\n"
        "## Top 20 fichiers inclus\n\n"
        f"{rows}\n",
    )


def _empty_size_payload(inventory: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "zip_name": ZIP_NAME,
        "zip_size_bytes": 0,
        "top_20_largest_files_included": [],
        "heavy_files_excluded": [],
        "raw_zips_excluded": True,
        "full_parquet_excluded_count": len(inventory["full_parquet_excluded"]),
        "note": "audit-lite does not replace full local validation",
    }


def _render_inventory_markdown(inventory: dict[str, Any]) -> str:
    excluded_rows = "\n".join(
        f"- `{item['timeframe']}` : `{item['path']}` ({item['rows']} lignes)"
        for item in inventory["full_parquet_excluded"]
    )
    return f"""# Inventaire audit-lite V4.0

Ce rapport decrit les artefacts lourds exclus du ZIP `audit-lite`.

- Raw zips exclus : `{inventory['raw_zips_excluded']}`
- Parquet complets exclus : `{len(inventory['full_parquet_excluded'])}`
- Validation full locale remplacee : `false`
- Note : `audit-lite does not replace full local validation`

## Parquet scores exclus

{excluded_rows}

## Garantie de scope

Les validateurs de production ne sont pas relaches. Le ZIP audit-lite sert a transmettre le code, les rapports, les manifests, les checksums et l'attestation full locale. Il ne pretend pas revalider physiquement les 90 jours sans les donnees completes locales.
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
