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


VERSION = "V4.0"
REPORT_JSON = Path("reports/audit_lite/zip_smoke_v4_0.json")
REPORT_MD = Path("reports/audit_lite/zip_smoke_v4_0.md")


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
    with tempfile.TemporaryDirectory(prefix="galapagos-v4-0-smoke-") as tmp:
        extract_root = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(extract_root)
        entries = [path.relative_to(extract_root).as_posix() for path in extract_root.rglob("*") if path.is_file()]
        if any(entry.startswith("data/raw/public_market/") or entry.endswith(".zip") for entry in entries):
            errors.append("audit-lite ZIP must not contain raw zips or nested zips")
        forbidden_prefixes = ["data/research/", "reports/backtests/", "reports/strategies/", "orders/", "execution/", "models/"]
        forbidden_suffixes = (".parquet", ".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt")
        for entry in entries:
            if any(entry.startswith(prefix) for prefix in forbidden_prefixes):
                errors.append(f"forbidden file in audit-lite ZIP: {entry}")
            if entry.endswith(forbidden_suffixes):
                errors.append(f"forbidden binary artifact in audit-lite ZIP: {entry}")
        sys.path.insert(0, str(extract_root / "src"))
        try:
            for module in [
                "galapagos.datasets.expanded_window_validation",
                "galapagos.ml.expanded_window_validation",
                "galapagos.ml.expanded_window_robustness",
                "galapagos.ml.expanded_window_robustness_validation",
            ]:
                importlib.import_module(module)
        except Exception as exc:
            errors.append(f"module import failed: {exc}")
        manifest = _read_json(extract_root / "reports/manifests/expanded_ml_robustness_v4_0_manifest.json")
        report = _read_json(extract_root / "reports/ml/expanded_ml_robustness_v4_0.json")
        inventory = _read_json(extract_root / "reports/audit_lite/v4_0_artifact_inventory.json")
        attestation = _read_json(extract_root / "reports/audit_lite/v4_0_full_local_validation_attestation.json")
        if manifest != report:
            errors.append("V4.0 manifest/report mismatch inside audit-lite ZIP")
        for analysis in ["baseline_delta", "split_stability", "timeframe_stability", "label_shuffle_falsification", "feature_leakage_scan", "metric_forbidden_scan"]:
            if analysis not in manifest.get("analyses", {}):
                errors.append(f"missing V4.0 analysis in smoke: {analysis}")
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
                errors.append(f"V4.0 safety flag must be false: {key}")
        for key in ["public_read_only", "ml_enabled", "labels_enabled", "dataset_enabled"]:
            if safety.get(key) is not True:
                errors.append(f"V4.0 safety flag must be true: {key}")
        for flag in ["validator_passed", "tests_passed", "audit_lite_passed", "smoke_audit_lite_passed", "no_trading", "no_backtest", "no_orders", "no_strategy"]:
            if attestation.get(flag) is not True:
                errors.append(f"V4.0 attestation flag must be true: {flag}")
        if not inventory.get("audit_lite_does_not_replace_full_validation"):
            errors.append("audit-lite must not claim to replace full validation")
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
    return f"""# Smoke ZIP audit-lite V4.0

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
