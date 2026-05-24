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

from galapagos.datasets.schemas import DATASET_COLUMNS_V5_3, SPLIT_COLUMNS_V5_3


VERSION = "V5.3"
REPORT_JSON = Path("reports/audit_lite/zip_smoke_v5_3.json")
REPORT_MD = Path("reports/audit_lite/zip_smoke_v5_3.md")
DATASET_SAMPLES = [
    f"data/audit_lite/v5_3/datasets/timeframe={timeframe}/sample.parquet" for timeframe in ["1m", "5m", "15m", "1h"]
]
SPLIT_SAMPLES = [
    f"data/audit_lite/v5_3/splits/timeframe={timeframe}/sample.parquet" for timeframe in ["1m", "5m", "15m", "1h"]
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
    with tempfile.TemporaryDirectory(prefix="galapagos-v5-3-smoke-") as tmp:
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
                        "from galapagos.datasets.max_history_window import TIMEFRAMES_V5_3, dataset_output_path",
                        "from galapagos.datasets.max_history_window_quality import assess_max_history_dataset_quality",
                        "from galapagos.datasets.max_history_window_validation import validate_max_history_offline_supervised_dataset_v5_3",
                        "from galapagos.datasets.schemas import DATASET_COLUMNS_V5_3, SPLIT_COLUMNS_V5_3",
                        "assert DATASET_COLUMNS_V5_3[0] == 'source'",
                        "assert SPLIT_COLUMNS_V5_3[-1] == 'walk_forward_group'",
                        "assert TIMEFRAMES_V5_3 == ['1m', '5m', '15m', '1h']",
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

        manifest = _read_json(extract_root / "reports/manifests/max_history_offline_supervised_dataset_v5_3_manifest.json")
        report = _read_json(extract_root / "reports/datasets/max_history_offline_supervised_dataset_v5_3.json")
        inventory = _read_json(extract_root / "reports/audit_lite/v5_3_artifact_inventory.json")
        summary = _read_json(extract_root / "reports/audit_lite/v5_3_parquet_summary.json")
        if manifest != report:
            errors.append("V5.3 manifest/report mismatch inside audit-lite ZIP")
        if manifest.get("version") != VERSION or manifest.get("status") != "PASS":
            errors.append("V5.3 manifest status/version invalid inside audit-lite ZIP")
        if not inventory.get("audit_lite_does_not_replace_full_validation"):
            errors.append("audit-lite must not claim to replace full validation")
        if set(summary.get("datasets", {})) != {"1m", "5m", "15m", "1h"}:
            errors.append("V5.3 parquet summary datasets mismatch")
        if set(summary.get("splits", {})) != {"1m", "5m", "15m", "1h"}:
            errors.append("V5.3 parquet summary splits mismatch")
        for sample in DATASET_SAMPLES:
            frame = pd.read_parquet(extract_root / sample, engine="pyarrow")
            if list(frame.columns) != DATASET_COLUMNS_V5_3:
                errors.append(f"dataset sample schema mismatch: {sample}")
        for sample in SPLIT_SAMPLES:
            frame = pd.read_parquet(extract_root / sample, engine="pyarrow")
            if list(frame.columns) != SPLIT_COLUMNS_V5_3:
                errors.append(f"split sample schema mismatch: {sample}")
            if frame["walk_forward_group"].isna().any():
                errors.append(f"split sample missing walk_forward_group: {sample}")
        safety = manifest.get("safety", {})
        if safety.get("public_read_only") is not True or safety.get("dataset_enabled") is not True:
            errors.append("V5.3 public_read_only and dataset_enabled must be true")
        for key in [
            "authentication_used",
            "api_key_used",
            "private_endpoint_used",
            "orders_enabled",
            "paper_live_enabled",
            "trading_enabled",
            "ml_enabled",
            "backtest_enabled",
            "strategy_enabled",
            "execution_enabled",
        ]:
            if safety.get(key) is not False:
                errors.append(f"V5.3 safety flag must be false: {key}")
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
    return f"""# Smoke ZIP audit-lite V5.3

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
