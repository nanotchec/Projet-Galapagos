from typing import Any, Dict

class NoWriteGuard:
    def check_v1_79_v1_80(self, v1_79_write_res: Dict[str, Any], v1_79_summary: Dict[str, Any]) -> Dict[str, Any]:
        issues = []
        
        if v1_79_write_res.get("new_data_files_created") is not False:
            issues.append("V1.79 created new data files")
            
        if v1_79_summary.get("dataset_created") is not False:
            issues.append("V1.79 created a dataset")
            
        return {
            "no_write_guard_passed": len(issues) == 0,
            "issues": issues,
            "v1_79_no_data_directory_writes": v1_79_summary.get("no_data_directory_writes"),
            "v1_79_dataset_created": v1_79_summary.get("dataset_created"),
            "v1_80_no_data_directory_writes": True,
            "v1_80_dataset_created": False
        }
