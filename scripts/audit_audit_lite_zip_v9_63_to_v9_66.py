from __future__ import annotations

import argparse
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path


REPORT_JSON = Path("reports/audit_lite/zip_audit_v9_63_to_v9_66.json")
REPORT_MD = Path("reports/audit_lite/zip_audit_v9_63_to_v9_66.md")
VERSION = "V9.63_to_V9.66"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True)
    args = parser.parse_args()
    zip_path = Path(args.zip)
    errors: list[str] = []
    warnings: list[str] = []
    files: list[str] = []
    if not zip_path.is_file():
        errors.append(f"missing zip: {zip_path}")
    else:
        with zipfile.ZipFile(zip_path) as zf:
            files = zf.namelist()
            for name in files:
                lowered = name.casefold()
                if lowered.startswith(("data/research/", "data/raw/", "data/silver/")):
                    errors.append(f"forbidden data file in zip: {name}")
                if lowered.endswith((".sha256.json", ".sha256.txt")):
                    errors.append(f"forbidden sidecar in zip: {name}")
                if any(token in lowered for token in ["models/", "checkpoints/", "backtests/", "strategies/", "orders/", "execution/", ".env", ".pem", ".key"]):
                    errors.append(f"forbidden path in zip: {name}")
                if lowered.endswith((".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt")):
                    errors.append(f"forbidden model artifact in zip: {name}")
            required = [
                "reports/research_decisions/label_redesign_chain_v9_63_to_v9_66.json",
                "reports/audit_lite/v9_63_to_v9_66_command_results.json",
                "src/galapagos/ml/redesigned_label_5y_offline_ml_v9_66.py",
            ]
            for required_name in required:
                if required_name not in files:
                    errors.append(f"missing required zip member: {required_name}")
    payload = {"version": VERSION, "created_at_utc": utc_now(), "zip_path": zip_path.as_posix(), "files_count": len(files), "status": "PASS" if not errors else "FAIL", "passed": not errors, "errors": errors, "warnings": warnings, "sidecars_present": any(name.endswith((".sha256.json", ".sha256.txt")) for name in files), "zip_fingerprints_present": False}
    write_json(REPORT_JSON, payload)
    write_text(REPORT_MD, f"# Audit ZIP {VERSION}\n\n- Status : `{payload['status']}`.\n- Fichiers : `{payload['files_count']}`.\n- Erreurs : `{len(errors)}`.\n")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
