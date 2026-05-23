from __future__ import annotations

import argparse
import importlib
import json
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Any

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.data.public_market.storage import read_parquet


VERSION = "V4.6"
REPORT_JSON = Path("reports/audit_lite/zip_smoke_v4_6.json")
REPORT_MD = Path("reports/audit_lite/zip_smoke_v4_6.md")


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
    previous_dont_write_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    with tempfile.TemporaryDirectory(prefix="galapagos-v4-6-smoke-") as tmp:
        extract_root = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(extract_root)
        entries = [path.relative_to(extract_root).as_posix() for path in extract_root.rglob("*") if path.is_file()]
        forbidden_prefixes = [
            "reports/backtests/",
            "reports/strategies/",
            "reports/signals/",
            "reports/predictions/",
            "orders/",
            "execution/",
            "models/",
            "checkpoints/",
            "data/research/v4_6/backtests/",
            "data/research/v4_6/strategies/",
            "data/research/v4_6/orders/",
            "data/research/v4_6/execution/",
            "data/research/v4_6/models/",
            "data/research/v4_6/checkpoints/",
        ]
        for entry in entries:
            path = Path(entry)
            if "__pycache__" in path.parts or path.suffix.casefold() in {".pyc", ".pyo"}:
                errors.append(f"forbidden Python cache found after extraction: {entry}")
            if entry.startswith("data/raw/public_market/") or entry.endswith(".zip"):
                errors.append(f"raw or nested zip found in audit-lite: {entry}")
            if any(entry.startswith(prefix) for prefix in forbidden_prefixes):
                errors.append(f"forbidden file in audit-lite ZIP: {entry}")
            if entry.endswith(".parquet") and not entry.startswith("data/audit_lite/v4_6/ml_scores/"):
                errors.append(f"full Parquet must not be included in audit-lite smoke: {entry}")
            if path.suffix.casefold() in {".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt"}:
                errors.append(f"forbidden model artifact in audit-lite ZIP: {entry}")
        sys.path.insert(0, str(extract_root / "src"))
        try:
            from galapagos.datasets.schemas import DATASET_COLUMNS_V4_5
            from galapagos.features.schemas import FEATURE_COLUMNS_V4_3
            from galapagos.labels.schemas import LABEL_COLUMNS_V4_4
            from galapagos.ml.one_year_window_validation import validate_one_year_offline_ml_research_v4_6
            from galapagos.ml.schemas import ML_SCORE_COLUMNS_V4_6

            if not FEATURE_COLUMNS_V4_3 or not LABEL_COLUMNS_V4_4 or not DATASET_COLUMNS_V4_5 or not ML_SCORE_COLUMNS_V4_6:
                errors.append("V4.6 smoke import probe returned empty schema constants")
            if not callable(validate_one_year_offline_ml_research_v4_6):
                errors.append("V4.6 smoke import probe validation callable missing")
            for module in [
                "galapagos.data.public_market.one_year_window",
                "galapagos.features.one_year_window",
                "galapagos.labels.one_year_window",
                "galapagos.datasets.one_year_window",
                "galapagos.ml.one_year_window",
                "galapagos.ml.one_year_window_validation",
            ]:
                importlib.import_module(module)
        except Exception as exc:
            errors.append(f"module import failed: {exc}")
        manifest = _read_json(extract_root / "reports/manifests/one_year_offline_ml_research_v4_6_manifest.json")
        report = _read_json(extract_root / "reports/ml/one_year_offline_ml_research_v4_6.json")
        parquet_summary = _read_json(extract_root / "reports/audit_lite/v4_6_parquet_summary.json")
        attestation = _read_json(extract_root / "reports/audit_lite/v4_6_full_local_validation_attestation.json")
        if manifest != report:
            errors.append("V4.6 manifest/report mismatch inside audit-lite ZIP")
        safety = manifest.get("safety", {})
        expected_false = [
            "authentication_used",
            "api_key_used",
            "private_endpoint_used",
            "orders_enabled",
            "paper_live_enabled",
            "trading_enabled",
            "backtest_enabled",
            "strategy_enabled",
            "execution_enabled",
        ]
        for key in expected_false:
            if safety.get(key) is not False:
                errors.append(f"V4.6 safety flag must be false: {key}")
        for key in ["public_read_only", "ml_enabled", "labels_enabled", "dataset_enabled"]:
            if safety.get(key) is not True:
                errors.append(f"V4.6 safety flag must be true: {key}")
        for flag in ["validator_passed", "tests_passed", "audit_lite_passed", "smoke_audit_lite_passed", "no_trading", "no_backtest", "no_orders", "no_persistent_model"]:
            if attestation.get(flag) is not True:
                errors.append(f"V4.6 attestation flag must be true: {flag}")
        sample_rows: dict[str, int] = {}
        for timeframe in ["1m", "5m", "15m", "1h"]:
            sample = read_parquet(extract_root / f"data/audit_lite/v4_6/ml_scores/timeframe={timeframe}/sample.parquet")
            if list(sample.columns) != parquet_summary["scores"][timeframe]["columns"]:
                errors.append(f"score sample columns mismatch for {timeframe}")
            sample_rows[timeframe] = int(len(sample))
        if not parquet_summary.get("audit_lite_does_not_replace_full_validation"):
            errors.append("audit-lite must not claim to replace full validation")
    sys.dont_write_bytecode = previous_dont_write_bytecode
    result = _result(zip_path, errors, warnings)
    result["sample_rows"] = sample_rows if "sample_rows" in locals() else {}
    return result


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
    return f"""# Smoke ZIP audit-lite V4.6

- Statut : `{status}`
- ZIP : `{result['zip_path']}`
- Taille : `{result['zip_size_bytes']}` octets
- Duree : `{result.get('smoke_duration_seconds')}` secondes

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
