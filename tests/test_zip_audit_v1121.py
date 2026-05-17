from __future__ import annotations

import importlib.util
import sys
import zipfile
from pathlib import Path


def _load_audit_zip():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "audit_clean_zip.py"
    sys.path.insert(0, str(script_path.parent))
    spec = importlib.util.spec_from_file_location("audit_clean_zip_script", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.audit_zip


def test_zip_audit_detects_forbidden_and_secret(tmp_path: Path) -> None:
    audit_zip = _load_audit_zip()
    zip_path = tmp_path / "bad.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr(".env", "FRED_" + "API_KEY=secret-value\n")
        archive.writestr("src/app.py", "print('ok')\n")
    payload = audit_zip(zip_path, write_report=False)
    assert payload["forbidden_count"] >= 1
    assert payload["secret_hits"] == [".env"]
    assert payload["clean_zip_ready_for_external_review"] is False


def test_zip_audit_detects_real_fred_key_and_missing_required(tmp_path: Path) -> None:
    audit_zip = _load_audit_zip()
    zip_path = tmp_path / "bad_fred.zip"
    fred_secret = "83e4134d" + "95ae580d" + "58cab1db" + "486c5058"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("src/galapagos/data/__init__.py", "")
        archive.writestr("reports/PROJECT_STATE.md", fred_secret)
    payload = audit_zip(zip_path, version="v1_12_2", write_report=False)
    assert "reports/PROJECT_STATE.md" in payload["secret_hits"]
    assert "src/galapagos/data/manifest.py" in payload["missing_required_files"]
    assert payload["source_package_data_present"] is True
