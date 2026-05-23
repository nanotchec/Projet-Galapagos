from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.labels.schemas import LABEL_COLUMNS_V4_4  # noqa: E402


VERSION = "V4.4"
REPORT_JSON = Path("reports/audit_lite/zip_smoke_v4_4.json")
REPORT_MD = Path("reports/audit_lite/zip_smoke_v4_4.md")
SAMPLES = [
    "data/audit_lite/v4_4/labels/timeframe=1m/sample.parquet",
    "data/audit_lite/v4_4/labels/timeframe=5m/sample.parquet",
    "data/audit_lite/v4_4/labels/timeframe=15m/sample.parquet",
    "data/audit_lite/v4_4/labels/timeframe=1h/sample.parquet",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True, dest="zip_path")
    args = parser.parse_args()
    started = time.perf_counter()
    result = smoke_zip(Path(args.zip_path).resolve())
    result["smoke_duration_seconds"] = round(time.perf_counter() - started, 3)
    _write_json(REPORT_JSON, result)
    _write_text(REPORT_MD, _render_markdown(result))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not result["passed"]:
        raise SystemExit(1)


def smoke_zip(zip_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not zip_path.exists():
        return _result(zip_path, [f"missing ZIP: {zip_path}"], warnings)
    with tempfile.TemporaryDirectory(prefix="galapagos-v4-4-smoke-") as tmp:
        extract_root = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(extract_root)
        entries = [path.relative_to(extract_root).as_posix() for path in extract_root.rglob("*") if path.is_file()]
        for entry in entries:
            path = Path(entry)
            if "__pycache__" in path.parts or path.suffix.casefold() in {".pyc", ".pyo"}:
                errors.append(f"forbidden Python cache found after extraction: {entry}")
            if entry.startswith("data/raw/public_market/") or entry.endswith(".zip"):
                errors.append(f"raw or nested zip found in audit-lite: {entry}")
            if entry.startswith("data/research/"):
                errors.append(f"full research artifact found in audit-lite: {entry}")
            if entry.startswith(("reports/backtests/", "reports/strategies/", "orders/", "execution/", "models/")):
                errors.append(f"forbidden file in audit-lite ZIP: {entry}")
            if path.suffix.casefold() in {".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt"}:
                errors.append(f"forbidden model artifact in audit-lite ZIP: {entry}")

        import_probe = subprocess.run(
            [
                sys.executable,
                "-c",
                "\n".join(
                    [
                        "from galapagos.labels.schemas import LABEL_COLUMNS_V4_4",
                        "from galapagos.labels.one_year_window import TIMEFRAMES_V4_4, output_path",
                        "from galapagos.labels.one_year_window_quality import EXPECTED_ROWS_V4_4",
                        "from galapagos.labels.one_year_window_validation import validate_one_year_label_factory_v4_4",
                        "assert EXPECTED_ROWS_V4_4['1m'] == 527040",
                        "print('imports_ok')",
                    ]
                ),
            ],
            cwd=extract_root,
            env={**os.environ, "PYTHONPATH": str(extract_root / "src")},
            capture_output=True,
            text=True,
            check=False,
        )
        if import_probe.returncode != 0 or "imports_ok" not in import_probe.stdout:
            errors.append(
                "module import failed: "
                f"returncode={import_probe.returncode}; stdout={import_probe.stdout.strip()}; stderr={import_probe.stderr.strip()}"
            )

        manifest = _read_json(extract_root / "reports/manifests/one_year_label_factory_v4_4_manifest.json")
        report = _read_json(extract_root / "reports/labels/one_year_label_factory_v4_4.json")
        inventory = _read_json(extract_root / "reports/audit_lite/v4_4_artifact_inventory.json")
        summary = _read_json(extract_root / "reports/audit_lite/v4_4_parquet_summary.json")
        if manifest != report:
            errors.append("V4.4 manifest/report mismatch inside audit-lite ZIP")
        if manifest.get("version") != VERSION or manifest.get("status") != "PASS":
            errors.append("V4.4 manifest status/version invalid inside audit-lite ZIP")
        if len(inventory.get("raw_files_excluded", [])) != 366:
            errors.append("V4.4 raw inventory must represent 366 raw zips")
        if not inventory.get("audit_lite_does_not_replace_full_validation"):
            errors.append("audit-lite must not claim to replace full validation")
        if set(summary.get("labels", {})) != {"1m", "5m", "15m", "1h"}:
            errors.append("V4.4 parquet summary labels mismatch")
        for sample in SAMPLES:
            frame = pd.read_parquet(extract_root / sample, engine="pyarrow")
            if list(frame.columns) != LABEL_COLUMNS_V4_4:
                errors.append(f"sample schema mismatch: {sample}")
        safety = manifest.get("safety", {})
        if safety.get("public_read_only") is not True:
            errors.append("V4.4 public_read_only must be true")
        for key in [
            "authentication_used",
            "api_key_used",
            "private_endpoint_used",
            "orders_enabled",
            "paper_live_enabled",
            "trading_enabled",
            "ml_enabled",
            "dataset_enabled",
            "backtest_enabled",
            "strategy_enabled",
            "execution_enabled",
        ]:
            if safety.get(key) is not False:
                errors.append(f"V4.4 safety flag must be false: {key}")
        if safety.get("labels_enabled") is not True:
            errors.append("V4.4 labels_enabled must be true")
    return _result(zip_path, errors, warnings)


def _result(zip_path: Path, errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "zip_path": str(zip_path),
        "zip_size_bytes": zip_path.stat().st_size if zip_path.exists() else 0,
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def _render_markdown(result: dict[str, Any]) -> str:
    status = "PASS" if result["passed"] else "FAIL"
    errors = "\n".join(f"- {error}" for error in result["errors"]) or "- Aucune"
    return f"""# Smoke ZIP audit-lite V4.4

- Statut : `{status}`
- ZIP : `{result['zip_path']}`
- Taille : `{result['zip_size_bytes']}` octets
- Duree : `{result.get('smoke_duration_seconds')}` secondes
- Note : `audit-lite does not replace full local validation`

## Erreurs

{errors}
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
