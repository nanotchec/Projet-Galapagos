import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

class PytestAudit:
    def run_audit(self, test_file: Path) -> Dict[str, Any]:
        if not test_file.exists():
            return {
                "pytest_executed": False,
                "pytest_exit_code": -1,
                "pytest_failed_count": 0,
                "pytest_passed_count": 0,
                "pytest_test_count_observed": 0,
                "pytest_report_present": False,
                "reported_test_count_matches_pytest": False
            }

        # Run pytest
        completed = subprocess.run([sys.executable, "-m", "pytest", "-q", str(test_file)], capture_output=True, text=True)
        test_output = completed.stdout + completed.stderr
        exit_code = completed.returncode
        
        # Count tests
        passed_match = re.search(r"(\d+) passed", test_output)
        failed_match = re.search(r"(\d+) failed", test_output)
        
        passed_count = int(passed_match.group(1)) if passed_match else 0
        failed_count = int(failed_match.group(1)) if failed_match else 0
        total_count = passed_count + failed_count

        return {
            "pytest_executed": True,
            "pytest_exit_code": exit_code,
            "pytest_failed_count": failed_count,
            "pytest_passed_count": passed_count,
            "pytest_test_count_observed": total_count,
            "pytest_report_present": True,
            "reported_test_count_matches_pytest": failed_count == 0
        }
