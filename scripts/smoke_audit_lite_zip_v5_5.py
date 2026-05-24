from __future__ import annotations

import argparse
import importlib
import json
import os
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Any

import _bootstrap

_bootstrap.bootstrap_src_path()


VERSION = "V5.5"
REPORT_JSON = Path("reports/audit_lite/zip_smoke_v5_5.json")
REPORT_MD = Path("reports/audit_lite/zip_smoke_v5_5.md")


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
    collect_result: dict[str, Any] = {"executed": False}
    if not zip_path.exists():
        return _result(zip_path, [f"missing ZIP: {zip_path}"], warnings, collect_result)
    with tempfile.TemporaryDirectory(prefix="galapagos-v5-5-smoke-") as tmp:
        extract_root = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(extract_root)
        entries = [path.relative_to(extract_root).as_posix() for path in extract_root.rglob("*") if path.is_file()]
        errors.extend(_forbidden_entry_errors(entries))
        sys.path.insert(0, str(extract_root / "src"))
        previous_dont_write_bytecode = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        try:
            imports = {
                "galapagos.ml.max_history_robustness": "run_max_history_ml_robustness_v5_5",
                "galapagos.ml.max_history_robustness_validation": "validate_max_history_ml_robustness_v5_5",
                "galapagos.ml.schemas": "ML_SCORE_COLUMNS_V5_4",
            }
            for module_name, attribute in imports.items():
                module = importlib.import_module(module_name)
                if not hasattr(module, attribute):
                    errors.append(f"missing import attribute: {module_name}.{attribute}")
        except Exception as exc:
            errors.append(f"module import failed: {exc}")
        finally:
            sys.dont_write_bytecode = previous_dont_write_bytecode
        post_import_entries = [path.relative_to(extract_root).as_posix() for path in extract_root.rglob("*") if path.is_file()]
        errors.extend(_forbidden_entry_errors(post_import_entries))
        manifest = _read_json(extract_root / "reports/manifests/max_history_ml_robustness_v5_5_manifest.json")
        report = _read_json(extract_root / "reports/ml/max_history_ml_robustness_v5_5.json")
        inventory = _read_json(extract_root / "reports/audit_lite/v5_5_artifact_inventory.json")
        attestation = _read_json(extract_root / "reports/audit_lite/v5_5_full_local_validation_attestation.json")
        if manifest != report:
            errors.append("V5.5 manifest/report mismatch inside audit-lite ZIP")
        for analysis in [
            "baseline_delta",
            "split_stability",
            "timeframe_stability",
            "walk_forward_stability",
            "label_shuffle_falsification",
            "feature_leakage_scan",
            "metric_forbidden_scan",
        ]:
            if analysis not in manifest.get("analyses", {}):
                errors.append(f"missing V5.5 analysis in smoke: {analysis}")
        safety = manifest.get("safety", {})
        for key in ["authentication_used", "api_key_used", "private_endpoint_used", "orders_enabled", "paper_live_enabled", "trading_enabled", "backtest_enabled", "strategy_enabled", "execution_enabled"]:
            if safety.get(key) is not False:
                errors.append(f"V5.5 safety flag must be false: {key}")
        for key in ["public_read_only", "ml_enabled", "labels_enabled", "dataset_enabled"]:
            if safety.get(key) is not True:
                errors.append(f"V5.5 safety flag must be true: {key}")
        findings = manifest.get("findings", {})
        for key in ["robust_edge_claimed", "strategy_validated", "backtest_performed", "actionable_signal_produced"]:
            if findings.get(key) is not False:
                errors.append(f"V5.5 finding must be false: {key}")
        for flag in ["validator_passed", "tests_passed", "audit_lite_passed", "smoke_audit_lite_passed", "no_trading", "no_backtest", "no_orders", "no_strategy"]:
            if attestation.get(flag) is not True:
                errors.append(f"V5.5 attestation flag must be true: {flag}")
        if not inventory.get("audit_lite_does_not_replace_full_validation"):
            errors.append("audit-lite must not claim to replace full validation")
        collect_result = _run_collect_only(extract_root)
        if collect_result["returncode"] != 0:
            errors.append("V5.5 audit-lite pytest collect-only failed")
    return _result(zip_path, errors, warnings, collect_result)


def _run_collect_only(extract_root: Path) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=extract_root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "executed": True,
        "command": "PYTHONPATH=src python -m pytest --collect-only -q",
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
    }


def _forbidden_entry_errors(entries: list[str]) -> list[str]:
    errors: list[str] = []
    forbidden_prefixes = ["data/raw/", "data/research/", "reports/backtests/", "reports/strategies/", "orders/", "execution/", "models/", "checkpoints/"]
    forbidden_suffixes = (".parquet", ".pyc", ".pyo", ".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt", ".zip")
    for entry in entries:
        path = Path(entry)
        if "__pycache__" in path.parts:
            errors.append(f"forbidden Python cache found: {entry}")
        if any(entry.startswith(prefix) for prefix in forbidden_prefixes):
            errors.append(f"forbidden file in audit-lite ZIP: {entry}")
        if entry.endswith(forbidden_suffixes):
            errors.append(f"forbidden binary artifact in audit-lite ZIP: {entry}")
        if len(path.parts) == 2 and path.parts[0] == "scripts" and path.suffix == ".py" and (path.name.startswith("test_") or path.name.endswith("_test.py")):
            errors.append(f"forbidden pytest-collectible script found: {entry}")
    return errors


def _result(zip_path: Path, errors: list[str], warnings: list[str], collect_result: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "zip_path": str(zip_path),
        "zip_size_bytes": zip_path.stat().st_size if zip_path.exists() else 0,
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "pytest_collect_only": collect_result,
    }


def _render_markdown(result: dict[str, Any]) -> str:
    status = "PASS" if result["passed"] else "FAIL"
    errors = "\n".join(f"- {error}" for error in result["errors"]) or "- Aucune"
    return f"""# Smoke ZIP audit-lite V5.5

- Statut : `{status}`
- ZIP : `{result['zip_path']}`
- Taille : `{result['zip_size_bytes']}` octets
- Collect-only : `{result['pytest_collect_only'].get('returncode')}`
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
