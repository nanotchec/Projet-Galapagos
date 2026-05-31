from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


VERSION = "V9.56_to_V9.58"
REPORT_JSON_PATH = Path("reports/audit_lite/zip_smoke_v9_56_to_v9_58.json")
REPORT_MD_PATH = Path("reports/audit_lite/zip_smoke_v9_56_to_v9_58.md")


def smoke_zip_v9_56_to_v9_58(zip_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    checks: dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="galapagos_v9_56_to_v9_58_smoke_") as tmp:
        tmp_path = Path(tmp)
        try:
            with zipfile.ZipFile(zip_path) as archive:
                archive.extractall(tmp_path)
            checks["extract"] = True
        except Exception as exc:
            return _report(zip_path, checks, [f"extract failed: {type(exc).__name__}: {exc}"])
        sys.path.insert(0, (tmp_path / "src").as_posix())
        try:
            importlib.import_module("galapagos.research.funding_tail_resolution_v9_56")
            importlib.import_module("galapagos.features.funding_only_feature_store_v9_57")
            importlib.import_module("galapagos.features.funding_only_feature_store_validation_v9_58")
            checks["imports"] = True
        except Exception as exc:
            errors.append(f"import failed: {type(exc).__name__}: {exc}")
            checks["imports"] = False
        try:
            import pyarrow  # noqa: F401

            checks["pyarrow_available"] = True
        except Exception as exc:
            errors.append(f"pyarrow or parquet engine missing: {type(exc).__name__}: {exc}")
            checks["pyarrow_available"] = False
        if shutil.which("pytest"):
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "--collect-only", "-q", "tests/research/test_funding_tail_resolution_v9_56.py", "tests/features/test_funding_only_feature_store_v9_57.py"],
                cwd=tmp_path,
                text=True,
                capture_output=True,
                timeout=60,
            )
            checks["pytest_collect_only_returncode"] = result.returncode
            if result.returncode != 0:
                errors.append(f"pytest collect-only failed: {result.stdout[-500:]} {result.stderr[-500:]}")
        try:
            from galapagos.features.funding_only_feature_store_validation_v9_58_validation import validate_funding_only_feature_store_validation_file_v9_58
            from galapagos.features.funding_only_feature_store_v9_57_validation import validate_funding_only_feature_store_file_v9_57
            from galapagos.research.funding_tail_resolution_v9_56_validation import validate_funding_tail_resolution_file_v9_56

            checks["v9_56_validator"] = validate_funding_tail_resolution_file_v9_56(tmp_path, mode="audit-lite")
            checks["v9_57_validator"] = validate_funding_only_feature_store_file_v9_57(tmp_path, mode="audit-lite")
            checks["v9_58_validator"] = validate_funding_only_feature_store_validation_file_v9_58(tmp_path, mode="audit-lite")
            for key in ["v9_56_validator", "v9_57_validator", "v9_58_validator"]:
                if checks[key].get("passed") is not True:
                    errors.append(f"{key} failed: {checks[key].get('errors')}")
        except Exception as exc:
            errors.append(f"validator smoke failed: {type(exc).__name__}: {exc}")
    return _report(zip_path, checks, errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True, dest="zip_path")
    args = parser.parse_args()
    report = smoke_zip_v9_56_to_v9_58(Path(args.zip_path))
    _write_json(REPORT_JSON_PATH, report)
    _write_text(REPORT_MD_PATH, "# Smoke ZIP V9.56 a V9.58\n\n" f"- Statut : `{report['status']}`.\n" f"- Erreurs : `{report['errors']}`.\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


def _report(zip_path: Path, checks: dict[str, Any], errors: list[str]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "created_at_utc": _utc_now(),
        "zip_path": zip_path.as_posix(),
        "status": "PASS" if not errors else "FAIL",
        "checks": checks,
        "errors": errors,
        "full_dataset_required": False,
        "sidecars_created": False,
        "zip_fingerprints_created": False,
    }


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
