from __future__ import annotations

import argparse
import importlib
import json
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd


VERSION = "V5.4"
SMOKE_JSON = Path("reports/audit_lite/zip_smoke_v5_4.json")
SMOKE_MD = Path("reports/audit_lite/zip_smoke_v5_4.md")


def smoke_zip(zip_path: Path) -> dict[str, Any]:
    start = time.perf_counter()
    errors: list[str] = []
    warnings: list[str] = []
    if not zip_path.exists():
        return _result(zip_path, errors=[f"missing zip: {zip_path}"], warnings=warnings, start=start)
    with tempfile.TemporaryDirectory(prefix="galapagos_v5_4_smoke_") as tmp:
        target = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(target)
        errors.extend(_check_required_files(target))
        errors.extend(_check_imports(target))
        errors.extend(_check_samples(target))
        errors.extend(_check_reports(target))
    return _result(zip_path, errors=errors, warnings=warnings, start=start)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True, dest="zip_path")
    args = parser.parse_args()
    result = smoke_zip(Path(args.zip_path).resolve())
    _write_reports(result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not result["passed"]:
        raise SystemExit(1)


def _check_required_files(root: Path) -> list[str]:
    required = [
        "reports/manifests/max_history_offline_ml_research_v5_4_manifest.json",
        "reports/ml/max_history_offline_ml_research_v5_4.json",
        "reports/audit_lite/v5_4_full_local_validation_attestation.json",
        "docs/max_history_offline_ml_research_v5_4.md",
    ]
    return [f"missing smoke file: {relative}" for relative in required if not (root / relative).exists()]


def _check_imports(root: Path) -> list[str]:
    import sys

    sys.path.insert(0, str(root / "src"))
    errors: list[str] = []
    for module in [
        "galapagos.ml.max_history_window",
        "galapagos.ml.max_history_window_metrics",
        "galapagos.ml.max_history_window_quality",
        "galapagos.ml.max_history_window_validation",
    ]:
        try:
            importlib.import_module(module)
        except Exception as exc:  # pragma: no cover - smoke diagnostic
            errors.append(f"import failed for {module}: {exc}")
    return errors


def _check_samples(root: Path) -> list[str]:
    errors: list[str] = []
    schema_module = importlib.import_module("galapagos.ml.schemas")
    expected_columns = schema_module.ML_SCORE_COLUMNS_V5_4
    for timeframe in ["1m", "5m", "15m", "1h"]:
        path = root / "data" / "audit_lite" / "v5_4" / "ml_scores" / f"timeframe={timeframe}" / "sample.parquet"
        if not path.exists():
            errors.append(f"missing score sample for {timeframe}")
            continue
        frame = pd.read_parquet(path, engine="pyarrow")
        if list(frame.columns) != expected_columns:
            errors.append(f"score sample schema mismatch for {timeframe}")
        forbidden = {"signal", "trading_signal", "order", "strategy", "pnl", "profit"}
        present = [column for column in frame.columns if column.casefold() in forbidden]
        if present:
            errors.append(f"forbidden score sample columns for {timeframe}: {present}")
    return errors


def _check_reports(root: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = root / "reports/manifests/max_history_offline_ml_research_v5_4_manifest.json"
    report_path = root / "reports/ml/max_history_offline_ml_research_v5_4.json"
    if manifest_path.exists() and report_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if manifest != report:
            errors.append("smoke manifest/report mismatch")
        safety = manifest.get("safety", {})
        for key in ["trading_enabled", "orders_enabled", "backtest_enabled", "strategy_enabled", "execution_enabled"]:
            if safety.get(key) is not False:
                errors.append(f"smoke safety flag must be false: {key}")
    markdown_path = root / "reports/ml/max_history_offline_ml_research_v5_4.md"
    if markdown_path.exists() and "strategy validated" in markdown_path.read_text(encoding="utf-8").casefold():
        errors.append("smoke markdown forbidden claim")
    return errors


def _result(zip_path: Path, *, errors: list[str], warnings: list[str], start: float) -> dict[str, Any]:
    return {
        "version": VERSION,
        "zip_path": str(zip_path),
        "zip_size_bytes": zip_path.stat().st_size if zip_path.exists() else 0,
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "smoke_duration_seconds": round(time.perf_counter() - start, 3),
    }


def _write_reports(result: dict[str, Any]) -> None:
    SMOKE_JSON.parent.mkdir(parents=True, exist_ok=True)
    SMOKE_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Smoke ZIP V5.4",
        "",
        f"- ZIP : `{result['zip_path']}`.",
        f"- Resultat : `{'PASS' if result['passed'] else 'FAIL'}`.",
        f"- Duree : `{result['smoke_duration_seconds']}` secondes.",
        f"- Erreurs : `{len(result['errors'])}`.",
    ]
    SMOKE_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
