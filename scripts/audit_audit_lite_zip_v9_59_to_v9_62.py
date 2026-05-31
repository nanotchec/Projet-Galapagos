from __future__ import annotations

import argparse
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


VERSION = "V9.59_to_V9.62"
REPORT_JSON_PATH = Path("reports/audit_lite/zip_audit_v9_59_to_v9_62.json")
REPORT_MD_PATH = Path("reports/audit_lite/zip_audit_v9_59_to_v9_62.md")
REQUIRED_SUFFIXES = [
    "src/galapagos/features/ohlcv_aggtrades_exact_funding_5y_feature_store_v9_59.py",
    "src/galapagos/datasets/ohlcv_aggtrades_exact_funding_5y_dataset_v9_60.py",
    "src/galapagos/datasets/ohlcv_aggtrades_exact_funding_5y_dataset_validation_v9_61.py",
    "src/galapagos/ml/ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62.py",
    "reports/research_decisions/funding_common_window_ml_chain_v9_59_to_v9_62.json",
    "reports/audit_lite/v9_59_to_v9_62_command_results.json",
]
FORBIDDEN_PREFIXES = ("data/raw/", "data/silver/", "data/research/", "data/gold/", "models/", "checkpoints/", "reports/backtests/", "reports/strategies/", "orders/", "execution/")
FORBIDDEN_SUFFIXES = (".sha256.json", ".sha256.txt", ".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt", ".pem", ".key")
FORBIDDEN_NAMES = {".DS_Store", ".env", "Icon", "Icon\r"}


def audit_zip_v9_59_to_v9_62(zip_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    names: list[str] = []
    if not zip_path.exists():
        errors.append(f"missing zip: {zip_path}")
    else:
        with zipfile.ZipFile(zip_path) as archive:
            names = archive.namelist()
            for name in names:
                path = Path(name)
                if path.name in FORBIDDEN_NAMES:
                    errors.append(f"forbidden name in zip: {name}")
                if any(name.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
                    errors.append(f"forbidden data prefix in zip: {name}")
                if any(name.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES):
                    errors.append(f"forbidden suffix in zip: {name}")
                if name.endswith(".json"):
                    try:
                        payload = json.loads(archive.read(name).decode("utf-8"))
                    except Exception as exc:
                        errors.append(f"invalid json {name}: {type(exc).__name__}: {exc}")
                        continue
                    if _contains_forbidden_zip_field(payload):
                        errors.append(f"zip fingerprint field forbidden in {name}")
    for required in REQUIRED_SUFFIXES:
        if required not in names:
            errors.append(f"missing required file: {required}")
    payload = {
        "version": VERSION,
        "created_at_utc": _utc_now(),
        "zip_path": zip_path.as_posix(),
        "files_count": len(names),
        "status": "PASS" if not errors else "FAIL",
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "sidecars_present": any(name.endswith((".sha256.json", ".sha256.txt")) for name in names),
        "zip_fingerprints_present": False,
    }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True, dest="zip_path")
    args = parser.parse_args()
    report = audit_zip_v9_59_to_v9_62(Path(args.zip_path))
    _write_json(REPORT_JSON_PATH, report)
    _write_text(REPORT_MD_PATH, "# Audit ZIP V9.59 a V9.62\n\n" f"- Statut : `{report['status']}`.\n" f"- Fichiers : `{report['files_count']}`.\n" f"- Erreurs : `{report['errors']}`.\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


def _contains_forbidden_zip_field(payload: Any) -> bool:
    if isinstance(payload, dict):
        for key, value in payload.items():
            lowered = str(key).casefold()
            if "zip_sha256" in lowered or lowered.endswith("_sha256") or lowered == "sha256":
                return True
            if _contains_forbidden_zip_field(value):
                return True
    elif isinstance(payload, list):
        return any(_contains_forbidden_zip_field(item) for item in payload)
    return False


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
