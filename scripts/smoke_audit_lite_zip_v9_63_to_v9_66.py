from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path


REPORT_JSON = Path("reports/audit_lite/zip_smoke_v9_63_to_v9_66.json")
REPORT_MD = Path("reports/audit_lite/zip_smoke_v9_63_to_v9_66.md")
VERSION = "V9.63_to_V9.66"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True)
    args = parser.parse_args()
    zip_path = Path(args.zip).resolve()
    errors: list[str] = []
    checks: dict[str, object] = {}
    with tempfile.TemporaryDirectory(prefix="galapagos_v9_63_to_v9_66_smoke_") as tmp:
        tmp_path = Path(tmp)
        try:
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(tmp_path)
            checks["extract"] = True
        except Exception as exc:
            errors.append(f"extract failed: {exc}")
            checks["extract"] = False
        if not errors:
            pyarrow_check = run_cmd([sys.executable, "-c", "import pyarrow"], tmp_path, timeout=20)
            checks["pyarrow_available"] = pyarrow_check.returncode == 0
            if pyarrow_check.returncode != 0:
                errors.append("pyarrow is required for audit-lite smoke")
            import_check = run_cmd([sys.executable, "-c", "import sys; sys.path.insert(0, 'src'); import galapagos.research.label_redesign_diagnostic_v9_63; import galapagos.labels.redesigned_5y_label_factory_v9_64; import galapagos.datasets.redesigned_label_5y_dataset_v9_65; import galapagos.ml.redesigned_label_5y_offline_ml_v9_66"], tmp_path, timeout=30)
            checks["imports"] = import_check.returncode == 0
            if import_check.returncode != 0:
                errors.append(f"import failed: {import_check.stderr[-500:]}")
            collect = run_cmd([sys.executable, "-m", "pytest", "--collect-only", "-q"], tmp_path, timeout=60, extra_env={"PYTHONPATH": "src"})
            checks["pytest_collect_only_returncode"] = collect.returncode
            if collect.returncode != 0:
                errors.append(f"pytest collect-only failed: {(collect.stdout + collect.stderr)[-1000:]}")
            for script in [
                "scripts/validate_label_redesign_diagnostic_v9_63.py",
                "scripts/validate_redesigned_5y_label_factory_v9_64.py",
                "scripts/validate_redesigned_label_5y_dataset_v9_65.py",
                "scripts/validate_redesigned_label_5y_offline_ml_v9_66.py",
            ]:
                result = run_cmd([sys.executable, script], tmp_path, timeout=30)
                checks[script] = result.returncode
                if result.returncode != 0:
                    errors.append(f"{script} failed: {result.stdout[-300:]} {result.stderr[-300:]}")
    payload = {"version": VERSION, "created_at_utc": utc_now(), "zip_path": zip_path.name, "status": "PASS" if not errors else "FAIL", "passed": not errors, "checks": checks, "errors": errors, "full_dataset_required": False, "sidecars_created": False, "zip_fingerprints_created": False}
    write_json(REPORT_JSON, payload)
    write_text(REPORT_MD, f"# Smoke ZIP {VERSION}\n\n- Status : `{payload['status']}`.\n- Erreurs : `{len(errors)}`.\n")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


def run_cmd(cmd: list[str], cwd: Path, timeout: int, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = None
    if extra_env:
        import os

        env = {**os.environ, **extra_env}
    return subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, env=env)


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
