"""Compatibility wrapper for V1.20 intrabar report validation tests."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def validate_reports(version: str, reports_dir: Path | None = None) -> dict[str, Any]:
    v_norm = version.replace(".", "_")
    if reports_dir is None:
        reports_dir = Path("reports/research")

    download_path = reports_dir / f"intrabar_history_download_{v_norm}.json"
    quality_path = reports_dir / f"intrabar_data_quality_{v_norm}.json"
    lineage_path = reports_dir / f"intrabar_data_lineage_{v_norm}.json"
    eval_path = reports_dir / f"trade_ledger_intrabar_eval_{v_norm}.json"
    issues = []

    for path in [download_path, quality_path, lineage_path, eval_path]:
        if not path.exists():
            issues.append(f"Missing report: {path.name}")
    if issues:
        return {"status": "INTRABAR_REPORTS_INCONSISTENT", "issues": issues, "version": version}

    download = json.loads(download_path.read_text(encoding="utf-8"))
    quality = json.loads(quality_path.read_text(encoding="utf-8"))
    lineage = json.loads(lineage_path.read_text(encoding="utf-8"))
    evaluation = json.loads(eval_path.read_text(encoding="utf-8"))

    lineage_rows = lineage.get("rows")
    quality_rows = quality.get("rows")
    if lineage_rows != quality_rows:
        issues.append(f"Row mismatch: Lineage={lineage_rows}, Quality={quality_rows}")
    if lineage.get("first_timestamp") != quality.get("start_time"):
        issues.append(
            f"Start timestamp mismatch: Lineage={lineage.get('first_timestamp')}, "
            f"Quality={quality.get('start_time')}"
        )
    eval_meta = evaluation.get("intrabar_metadata", {})
    if eval_meta.get("rows") != lineage_rows:
        issues.append(f"Eval row mismatch: Eval={eval_meta.get('rows')}, Lineage={lineage_rows}")
    if download.get("status") == "dry_run" and evaluation.get("intrabar_metadata"):
        issues.append("Download report claims dry_run but Evaluation used data")

    policy_metrics = evaluation.get("policy_metrics", {})
    ratios = [metric.get("evaluated_ratio", 0) for metric in policy_metrics.values()]
    avg_ratio = sum(ratios) / len(ratios) if ratios else 0
    status = "INTRABAR_REPORTS_CONSISTENT" if not issues else "INTRABAR_REPORTS_INCONSISTENT"
    return {
        "status": status,
        "version": version,
        "issues": issues,
        "metrics": {"evaluated_ratio": avg_ratio},
    }
