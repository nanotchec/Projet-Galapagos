import subprocess
import sys
import os
from pathlib import Path
from typing import Any, Dict

class ScriptPortabilityAudit:
    def check_portability(self, script_path: Path, args: list[str] = None) -> Dict[str, Any]:
        if not script_path.exists():
            return {"script": str(script_path), "portable": False, "error": "Not found"}

        # Try to run with just 'python scripts/...' from root
        # We simulate this by NOT setting PYTHONPATH and running from root
        env = os.environ.copy()
        if "PYTHONPATH" in env:
            del env["PYTHONPATH"]
        
        cmd = [sys.executable, str(script_path)] + (args or [])
        
        try:
            # We use --help or similar to avoid actual execution if possible, 
            # or just rely on the fact that these scripts have --version check first
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                cwd=Path.cwd()
            )
            # If it fails with ModuleNotFoundError, it's not portable
            is_portable = "ModuleNotFoundError" not in result.stderr
            return {
                "script": str(script_path),
                "portable": is_portable,
                "exit_code": result.returncode,
                "stderr_preview": result.stderr[:500]
            }
        except Exception as e:
            return {"script": str(script_path), "portable": False, "error": str(e)}

    def audit_all_scripts(self, version: str) -> Dict[str, Any]:
        scripts = [
            "scripts/run_microstructure_data_contract_approval_intake_corrective_v1_81_5.py",
            "scripts/validate_microstructure_data_contract_approval_intake_corrective_v1_81_5_reports.py"
        ]
        
        results = {}
        all_portable = True
        for s in scripts:
            res = self.check_portability(Path(s), ["--help"])
            results[s] = res
            if not res.get("portable", False):
                all_portable = False
                
        return {
            "scripts_portable_without_manual_pythonpath": all_portable,
            "validator_script_portable_without_manual_pythonpath": results.get(scripts[1], {}).get("portable", False),
            "run_script_portable_without_manual_pythonpath": results.get(scripts[0], {}).get("portable", False),
            "details": results
        }
