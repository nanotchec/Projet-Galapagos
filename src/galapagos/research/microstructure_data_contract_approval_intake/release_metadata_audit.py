import re
import json
from pathlib import Path
from typing import Any, Dict

class ReleaseMetadataAudit:
    def audit_release(self, version: str) -> Dict[str, Any]:
        root = Path.cwd()
        summary_path = root / "reports/current/latest_summary.md"
        metrics_path = root / "reports/current/latest_metrics.json"
        state_path = root / "reports/PROJECT_STATE.json"
        index_path = root / "reports/REPORT_INDEX.md"

        # 1. Latest Summary Check
        latest_summary_version = "UNKNOWN"
        if summary_path.exists():
            with open(summary_path) as f:
                content = f.read()
                m = re.search(r"Version:\s*(V1\.[0-9]+\.[0-9]+)", content)
                if m: latest_summary_version = m.group(1)
        
        # 2. Latest Metrics Check
        latest_metrics_version = "UNKNOWN"
        if metrics_path.exists():
            with open(metrics_path) as f:
                data = json.load(f)
                latest_metrics_version = data.get("version", "UNKNOWN")

        # 3. Project State Check
        project_state_version = "UNKNOWN"
        if state_path.exists():
            with open(state_path) as f:
                data = json.load(f)
                project_state_version = data.get("version", "UNKNOWN")

        # 4. Report Index Check
        report_index_references_target = False
        if index_path.exists():
            with open(index_path) as f:
                content = f.read()
                # Check for [V1.81.6] or ## V1.81.6
                report_index_references_target = f"[{version}]" in content or f"## {version}" in content

        v_suffix = version.replace(".", "_").lower()
        
        return {
            "latest_summary_version": latest_summary_version,
            "latest_metrics_version": latest_metrics_version,
            "project_state_version": project_state_version,
            f"report_index_references_{v_suffix}": report_index_references_target,
            "latest_summary_stale": latest_summary_version != version,
            f"report_index_missing_{v_suffix}": not report_index_references_target
        }
