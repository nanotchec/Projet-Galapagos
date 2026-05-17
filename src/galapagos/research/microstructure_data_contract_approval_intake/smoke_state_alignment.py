import json
from pathlib import Path
from typing import Any, Dict

class SmokeStateAlignment:
    def check_alignment(self, 
                       smoke_report_path: Path, 
                       summary_path: Path, 
                       metrics_path: Path, 
                       state_path: Path) -> Dict[str, Any]:
        
        results = {
            "zip_smoke_test_matches_summary": False,
            "zip_smoke_test_matches_latest_metrics": False,
            "zip_smoke_test_matches_project_state": False,
            "smoke_test_passed_consistent": False,
            "smoke_passed_count_consistent": False,
            "issues": []
        }

        if not smoke_report_path.exists():
            results["issues"].append(f"Missing smoke report: {smoke_report_path.name}")
            return results

        with open(smoke_report_path) as f:
            smoke_data = json.load(f)
        
        smoke_passed = smoke_data.get("smoke_test_passed", False)
        smoke_count = smoke_data.get("smoke_passed_count", 0)
        smoke_timeout = smoke_data.get("smoke_timeout_detected", True)
        # Generalize: detect any smoke_runs_full_v..._pytest_suite field set to True
        any_full_pytest = any(k.startswith("smoke_runs_full_v") and k.endswith("_pytest_suite") and v is True 
                             for k, v in smoke_data.items())
        
        smoke_heavy = (smoke_data.get("smoke_runs_audit_clean_zip_full_scan", True) or 
                      any_full_pytest)

        # Check Summary
        if summary_path.exists():
            with open(summary_path) as f:
                summary_data = json.load(f)
            res_sum = (smoke_passed == summary_data.get("smoke_test_passed") and 
                      smoke_count == summary_data.get("smoke_passed_count") and
                      not smoke_timeout and not smoke_heavy)
            results["zip_smoke_test_matches_summary"] = res_sum
            if not res_sum:
                results["issues"].append(f"Summary mismatch or invalid smoke state")

        # Check Metrics
        if metrics_path.exists():
            with open(metrics_path) as f:
                metrics_data = json.load(f)
            res_met = (smoke_passed == metrics_data.get("smoke_test_passed") and 
                      smoke_count == metrics_data.get("smoke_passed_count") and
                      not smoke_timeout and not smoke_heavy)
            results["zip_smoke_test_matches_latest_metrics"] = res_met
            if not res_met:
                results["issues"].append(f"Metrics mismatch or invalid smoke state")

        # Check State
        if state_path.exists():
            with open(state_path) as f:
                state_data = json.load(f)
            res_sta = (smoke_passed == state_data.get("smoke_test_passed") and 
                      smoke_count == state_data.get("smoke_passed_count") and
                      not smoke_timeout and not smoke_heavy)
            results["zip_smoke_test_matches_project_state"] = res_sta
            if not res_sta:
                results["issues"].append(f"Project state mismatch or invalid smoke state")

        results["smoke_test_passed_consistent"] = (results["zip_smoke_test_matches_summary"] and 
                                                  results["zip_smoke_test_matches_latest_metrics"] and 
                                                  results["zip_smoke_test_matches_project_state"] and
                                                  not smoke_timeout and not smoke_heavy)
        
        return results
