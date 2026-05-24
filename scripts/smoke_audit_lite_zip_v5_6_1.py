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


VERSION = "V5.6.1"
REPORT_JSON = Path("reports/audit_lite/zip_smoke_v5_6_1.json")
REPORT_MD = Path("reports/audit_lite/zip_smoke_v5_6_1.md")


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
    with tempfile.TemporaryDirectory(prefix="galapagos-v5-6-1-smoke-") as tmp:
        extract_root = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(extract_root)
        entries = [path.relative_to(extract_root).as_posix() for path in extract_root.rglob("*") if path.is_file()]
        errors.extend(_forbidden_entry_errors(entries))
        sys.path.insert(0, str(extract_root / "src"))
        sys.path.insert(0, str(extract_root / "scripts"))
        previous_dont_write_bytecode = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        try:
            module = importlib.import_module("validate_research_decision_gate_v5_6")
            result = module.validate_research_decision_gate_v5_6(extract_root)
            if result.get("passed") is not True:
                errors.append(f"V5.6.1 embedded validator failed: {result.get('errors')}")
        except Exception as exc:
            errors.append(f"module import or validation failed: {exc}")
        finally:
            sys.dont_write_bytecode = previous_dont_write_bytecode
        post_import_entries = [path.relative_to(extract_root).as_posix() for path in extract_root.rglob("*") if path.is_file()]
        errors.extend(_forbidden_entry_errors(post_import_entries))
        report = _read_json(extract_root / "reports/research_decisions/v5_6_research_decision_gate.json")
        inventory = _read_json(extract_root / "reports/audit_lite/v5_6_1_artifact_inventory.json")
        attestation = _read_json(extract_root / "reports/audit_lite/v5_6_1_full_local_validation_attestation.json")
        if report.get("version") != "V5.6" or report.get("correction_version") != VERSION:
            errors.append("V5.6.1 corrected report version mismatch inside audit-lite ZIP")
        if report.get("recommended_next_step") != "B. Ameliorer les features OHLCV avant multi-source.":
            errors.append("V5.6.1 recommended_next_step must be Advanced OHLCV")
        roadmap = report.get("roadmap", [])
        if not roadmap or roadmap[0].get("direction") != "Max Historical Advanced OHLCV Feature Expansion":
            errors.append("V5.6.1 roadmap must start with Advanced OHLCV Feature Expansion")
        if not inventory.get("audit_lite_does_not_replace_full_validation"):
            errors.append("audit-lite must not claim to replace full validation")
        for key in ["trading_enabled", "paper_live_enabled", "orders_enabled", "backtest_enabled", "strategy_enabled", "execution_enabled"]:
            if report.get("safety", {}).get(key) is not False:
                errors.append(f"V5.6.1 safety flag must be false: {key}")
        for key in ["strategy_validated", "model_validated_for_trading", "profitability_claimed", "real_trading_allowed"]:
            if report.get("claims", {}).get(key) is not False:
                errors.append(f"V5.6.1 claim flag must be false: {key}")
        for flag in ["validator_passed", "tests_passed", "audit_lite_passed", "smoke_audit_lite_passed", "no_trading", "no_backtest", "no_orders", "no_strategy"]:
            if attestation.get(flag) is not True:
                errors.append(f"V5.6.1 attestation flag must be true: {flag}")
        collect_result = _run_collect_only(extract_root)
        if collect_result["returncode"] != 0:
            errors.append("V5.6.1 audit-lite pytest collect-only failed")
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
    return f"""# Smoke ZIP audit-lite V5.6.1

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
