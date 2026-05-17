from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_make_clean_zip():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "make_clean_zip.py"
    spec = importlib.util.spec_from_file_location("make_clean_zip_script", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.make_clean_zip


def test_make_clean_zip_exclusions(tmp_path: Path) -> None:
    make_clean_zip = _load_make_clean_zip()
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print('ok')\n", encoding="utf-8")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "cache.json").write_text("{}", encoding="utf-8")
    (tmp_path / ".env").write_text("SECRET=1\n", encoding="utf-8")
    (tmp_path / "reports" / "evaluation").mkdir(parents=True)
    (tmp_path / "reports" / "evaluation" / "x.json").write_text("{}", encoding="utf-8")
    (tmp_path / "reports").mkdir(exist_ok=True)
    (tmp_path / "reports" / "PROJECT_STATE.md").write_text("state\n", encoding="utf-8")
    payload = make_clean_zip(version="vtest", dry_run=True, root=tmp_path)
    assert payload["forbidden_entries"] == []
    assert payload["zip_written"] is False


def test_make_clean_zip_includes_source_data_but_excludes_root_data(tmp_path: Path) -> None:
    make_clean_zip = _load_make_clean_zip()
    source_data = tmp_path / "src" / "galapagos" / "data"
    source_data.mkdir(parents=True)
    (source_data / "__init__.py").write_text("", encoding="utf-8")
    (source_data / "manifest.py").write_text("VALUE = 1\n", encoding="utf-8")
    root_data = tmp_path / "data"
    root_data.mkdir()
    (root_data / "secret.csv").write_text("x\n", encoding="utf-8")

    payload = make_clean_zip(version="v1.12.2", dry_run=True, root=tmp_path)

    assert "src/galapagos/data/__init__.py" in payload["included_preview"]
    assert any(item.startswith("data/") for item in payload["excluded_preview"])
