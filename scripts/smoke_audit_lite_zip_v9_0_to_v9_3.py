from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import zipfile
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


FORBIDDEN_FEATURES = {
    "future_log_return_h1",
    "direction_h1",
    "up_down_flat_h1",
    "label_valid_h1",
    "split",
    "walk_forward_group",
    "fold_id",
    "fold_role",
    "prediction",
    "signal",
    "trading_signal",
    "order",
    "pnl",
    "backtest",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True, dest="zip_path")
    args = parser.parse_args()
    zip_path = Path(args.zip_path).resolve()
    result = smoke_zip(zip_path)
    _write_reports(result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


def smoke_zip(zip_path: Path) -> dict:
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="galapagos_v9_smoke_") as tmp:
        extract_root = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(extract_root)
        env = os.environ.copy()
        env["PYTHONPATH"] = str(extract_root / "src")
        imports = [
            "galapagos.features.refined_ohlcv_trades",
            "galapagos.datasets.refined_ohlcv_trades_window",
            "galapagos.ml.refined_ohlcv_trades_window",
            "galapagos.ml.refined_strict_walk_forward",
        ]
        for module in imports:
            completed = subprocess.run(
                ["python", "-c", f"import {module}"],
                cwd=extract_root,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            if completed.returncode != 0:
                errors.append(f"import failed for {module}: {completed.stderr.strip()}")
        v90 = _read_json(extract_root / "reports/manifests/refined_ohlcv_trades_feature_store_v9_0_manifest.json")
        v93 = _read_json(extract_root / "reports/manifests/refined_strict_walk_forward_validation_v9_3_manifest.json")
        if v90.get("selected_features_count") != 18:
            errors.append("selected_features_count must be 18")
        selected = set(v90.get("selected_features", []))
        if selected & FORBIDDEN_FEATURES:
            errors.append(f"forbidden selected features: {sorted(selected & FORBIDDEN_FEATURES)}")
        if v93.get("feature_leakage_scan", {}).get("feature_leakage_detected") is not False:
            errors.append("V9.3 feature leakage scan did not pass")
        for key in ["robust_edge_claimed", "strategy_validated", "backtest_performed", "actionable_signal_produced", "walk_forward_validated_for_trading"]:
            if v93.get("findings", {}).get(key) is not False:
                errors.append(f"V9.3 finding must be false: {key}")
        sample = extract_root / "data/audit_lite/v9_0_to_v9_3/features/timeframe=1m/features_sample.parquet"
        if not sample.exists():
            errors.append("missing features sample parquet")
        collect = subprocess.run(
            ["python", "-m", "pytest", "--collect-only", "-q"],
            cwd=extract_root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        if collect.returncode != 0:
            errors.append(f"pytest collect-only failed: {collect.stdout[-1000:]} {collect.stderr[-1000:]}")
    return {"zip": str(zip_path), "passed": not errors, "errors": errors}


def _write_reports(result: dict) -> None:
    report_dir = Path("reports/audit_lite")
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "zip_smoke_v9_0_to_v9_3.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (report_dir / "zip_smoke_v9_0_to_v9_3.md").write_text(
        "# Smoke audit-lite V9.0 -> V9.3\n\n"
        f"- Resultat : `{'PASS' if result['passed'] else 'FAIL'}`.\n"
        f"- Erreurs : `{result['errors']}`.\n",
        encoding="utf-8",
    )


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
