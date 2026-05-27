from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


VERSION = "V9.4"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True, dest="zip_path")
    args = parser.parse_args()
    result = smoke_zip(Path(args.zip_path).resolve())
    _write_reports(result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


def smoke_zip(zip_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="galapagos_v9_4_smoke_") as tmp:
        extract_root = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(extract_root)
        env = os.environ.copy()
        env["PYTHONPATH"] = str(extract_root / "src")
        sys.path.insert(0, str(extract_root / "src"))
        try:
            errors.extend(_import_required_modules(extract_root, env))
            errors.extend(_check_reports(extract_root))
        finally:
            if str(extract_root / "src") in sys.path:
                sys.path.remove(str(extract_root / "src"))
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
        tests = subprocess.run(
            [
                "python",
                "-m",
                "pytest",
                "-q",
                "tests/research/test_refined_research_decision_gate_v9_4.py",
                "tests/validation/test_refined_research_decision_gate_v9_4_validator.py",
            ],
            cwd=extract_root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        if tests.returncode != 0:
            errors.append(f"V9.4 tests failed in ZIP: {tests.stdout[-1000:]} {tests.stderr[-1000:]}")
    return {"version": VERSION, "zip": str(zip_path), "passed": not errors, "errors": errors}


def _import_required_modules(extract_root: Path, env: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for module in [
        "galapagos.research.refined_research_decision_gate_v9_4",
        "galapagos.research.refined_research_decision_gate_v9_4_validation",
        "galapagos.validation.safety",
    ]:
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
    return errors


def _check_reports(extract_root: Path) -> list[str]:
    errors: list[str] = []
    decision = _read_json(extract_root / "reports/research_decisions/refined_research_decision_gate_v9_4.json")
    manifest = _read_json(extract_root / "reports/manifests/refined_research_decision_gate_v9_4_manifest.json")
    if decision.get("version") != VERSION or manifest.get("version") != VERSION:
        errors.append("V9.4 report or manifest version mismatch")
    if decision.get("research_decision") != "backtest_not_justified_refine_labels":
        errors.append("V9.4 decision mismatch")
    if decision.get("label_shuffle_assessment", {}).get("no_clear_edge_vs_shuffled_labels_count") != 21:
        errors.append("V9.4 label shuffle warning count mismatch")
    if any(value is not False for value in decision.get("findings", {}).values()):
        errors.append("V9.4 findings must remain false")
    return errors


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_reports(result: dict[str, Any]) -> None:
    report_dir = Path("reports/audit_lite")
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "zip_smoke_v9_4.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (report_dir / "zip_smoke_v9_4.md").write_text(
        "# Smoke ZIP V9.4\n\n"
        f"- Resultat : `{'PASS' if result['passed'] else 'FAIL'}`.\n"
        f"- Erreurs : `{result['errors']}`.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
