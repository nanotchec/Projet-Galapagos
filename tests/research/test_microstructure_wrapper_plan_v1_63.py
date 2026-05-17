import json
import subprocess
import tempfile
from pathlib import Path

def test_wrapper_plan_validator_rejects_missing_reports():
    script_path = Path("scripts/validate_microstructure_wrapper_plan_reports.py").resolve()
    cmd = [
        "python",
        str(script_path),
        "--version",
        "v1.63",
    ]
    with tempfile.TemporaryDirectory() as d:
        res = subprocess.run(cmd, cwd=d, capture_output=True, text=True)
        assert res.returncode != 0
        assert "Missing" in res.stdout or "Missing" in res.stderr

def test_wrapper_plan_validator_rejects_data_files():
    script_path = Path("scripts/validate_microstructure_wrapper_plan_reports.py").resolve()
    p = Path("dummy.parquet")
    p.touch()
    try:
        cmd = [
            "python",
            str(script_path),
            "--version",
            "v1.63",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        assert res.returncode != 0
        assert "forbidden data files" in res.stdout
    finally:
        p.unlink()

