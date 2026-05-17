"""V1.82.1 Validator – reads all mandatory reports and checks invariants.

Fails if:
- pytest_executed != true
- pytest_exit_code != 0
- pytest_failed_count != 0
- Any dry-run invariant is violated
- Any mandatory report is missing
- Latest summary mentions V1.81.16 as current
- REPORT_INDEX.md does not reference V1.82.1
"""
import argparse
import json
import sys
from pathlib import Path

SCRIPTS_ROOT = Path(__file__).resolve().parent
_PROJECT_ROOT_CANDIDATES = [
     SCRIPTS_ROOT.parent,           # scripts/ -> project root
     SCRIPTS_ROOT.parent.parent,    # scripts/ -> scripts/ -> grandparent
     Path.cwd(),                    # current working dir
     Path.cwd().parent,             # cwd's parent
]
PROJECT_ROOT = None
for _candidate in _PROJECT_ROOT_CANDIDATES:
     if (_candidate / "src").is_dir() and (_candidate / "scripts").is_dir():
         PROJECT_ROOT = _candidate
         break
if PROJECT_ROOT is None:
     PROJECT_ROOT = _PROJECT_ROOT_CANDIDATES[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v1_82_1")
    args = parser.parse_args()

    v_disp = "V1.82.1"
    v_norm = "v1_82_1"

     # ── Mandatory report paths ───────────────────────────────────────────
    reports = {
         "summary": PROJECT_ROOT
             / "reports/research/microstructure_data_contract_dryrun_summary_v1_82_1.json",
         "contract": PROJECT_ROOT
             / "reports/research/microstructure_data_contract_dryrun_contract_v1_82_1.json",
         "safety": PROJECT_ROOT
             / "reports/research/microstructure_data_contract_dryrun_safety_check_v1_82_1.json",
         "consistency": PROJECT_ROOT
             / "reports/research/microstructure_data_contract_dryrun_consistency_check_v1_82_1.json",
         "metrics": PROJECT_ROOT / "reports/current/latest_metrics.json",
         "project_state": PROJECT_ROOT / "reports/PROJECT_STATE.json",
         "report_index": PROJECT_ROOT / "reports/REPORT_INDEX.md",
         "code_review": PROJECT_ROOT / "docs/code_review_v1_82_1.md",
         "latest_summary": PROJECT_ROOT / "reports/current/latest_summary.md",
         "release_zip": PROJECT_ROOT / f"reports/release_zip_{v_norm}.json",
         "zip_audit": PROJECT_ROOT / f"reports/zip_audit_{v_norm}.json",
         "zip_smoke": PROJECT_ROOT / f"reports/zip_smoke_test_{v_norm}.json",
     }

    errors = []

     # ── Existence check ──────────────────────────────────────────────────
    for key, path in reports.items():
        if not path.exists():
            errors.append(f"Missing mandatory report: {path.name}")
        elif path.suffix == ".json":
             try:
                 with open(path) as f:
                     json.load(f)
             except json.JSONDecodeError as exc:
                 errors.append(f"Invalid JSON in {path.name}: {exc}")

    if errors:
        print(f"ERROR: V1.82.1 validation failed (existence):\n" + "\n".join(f"   - {e}" for e in errors))
        sys.exit(1)

     # ── Load data ────────────────────────────────────────────────────────
    loaded = {}
    text_keys = {"report_index", "latest_summary", "code_review"}
    for key, path in reports.items():
        if key in text_keys:
            loaded[key] = path.read_text(encoding="utf-8")
        else:
             with open(path) as f:
                 loaded[key] = json.load(f)

     # ── Summary invariants ───────────────────────────────────────────────
    inv_fields_str = {
         "dry_run_only": True,
         "reports_only": True,
         "network_executed": False,
         "data_directory_writes_allowed": False,
         "data_directory_write_attempted": False,
         "new_data_files_created": False,
         "no_data_directory_writes": True,
         "parquet_created": False,
         "csv_created": False,
         "sqlite_created": False,
         "jsonl_created": False,
         "db_created": False,
         "dataset_created": False,
         "research_dataset_updated": False,
         "materialization_executed": False,
         "data_contract_actual_write_executed": False,
         "theoretical_paths_only": True,
         "theoretical_schema_only": True,
         "theoretical_manifest_only": True,
         "physical_files_created_count": 0,
         "trading_allowed": False,
         "real_orders_possible": False,
         "no_real_trading": True,
         "ml_signal_validation_executed": False,
         "predictions_created": False,
         "labels_created": False,
         "targets_created": False,
         "holdout_executed": False,
         "codex_cli_called": False,
         "no_paper_live": True,
         "future_write_requires_new_human_approval": True,
     }

    def check_field(d, field, expected, context):
         if d.get(field) != expected:
             errors.append(f"{context}: {field}={d.get(field)} expected {expected}")

     # Check across summary, metrics, project_state
    for d_name, d_key in [
         ("summary", "summary"),
         ("metrics", "metrics"),
         ("project_state", "project_state"),
     ]:
         d = loaded[d_key]
         for field, expected in inv_fields_str.items():
             check_field(d, field, expected, f"{d_name}/{field}")

     # pytest checks
    for d_name, d_key in [("summary", "summary"), ("metrics", "metrics"), ("project_state", "project_state")]:
         d = loaded[d_key]
         if d.get("pytest_executed") is not True:
             errors.append(f"{d_name}: pytest_executed != True")
         if d.get("pytest_exit_code") != 0:
             errors.append(f"{d_name}: pytest_exit_code != 0")
         if d.get("pytest_failed_count") != 0:
             errors.append(f"{d_name}: pytest_failed_count != 0")

     # dryrun_preview_records_count <= 5
    for d_name, d_key in [("summary", "summary"), ("metrics", "metrics"), ("project_state", "project_state")]:
         d = loaded[d_key]
         if d.get("dryrun_preview_records_count", 0) > 5:
             errors.append(f"{d_name}: dryrun_preview_records_count > 5")

     # ── Release & consistency checks ─────────────────────────────────────
    release = loaded.get("release_zip", {})
    if release.get("release_ready_for_external_review") is not True:
         errors.append("release_zip: release_ready_for_external_review != True")

    if release.get("clean_zip_ready_for_external_review") is not True:
         errors.append("release_zip: clean_zip_ready_for_external_review != True")

    if release.get("blocking_reason") is not None:
         errors.append("release_zip: blocking_reason is not null")

    zip_audit = loaded.get("zip_audit", {})
    if zip_audit.get("clean_zip_ready_for_external_review") is not True:
         errors.append("zip_audit: clean_zip_ready_for_external_review != True")

    zip_smoke = loaded.get("zip_smoke", {})
    if zip_smoke.get("smoke_test_passed") is not True:
         errors.append("zip_smoke: smoke_test_passed != True")

     # ── Latest summary.md checks ─────────────────────────────────────────
    latest_summary_text = loaded["latest_summary"]
    if "V1.82.1" not in latest_summary_text:
         errors.append("latest_summary.md does not mention V1.82.1")
    if "V1.81.16" in latest_summary_text and "V1.81.16" in latest_summary_text.split("#")[1:][0]:
         errors.append("latest_summary.md still references V1.81.16 as current version")

     # ── REPORT_INDEX.md checks ───────────────────────────────────────────
    report_index_text = loaded["report_index"]
    if "v1_82_1" not in report_index_text:
         errors.append("REPORT_INDEX.md does not reference v1_82_1")

     # ── Code review presence ─────────────────────────────────────────────
     # This is optional for dry-run only, but let's check existence
     # code_review exists is not strictly mandatory for dry-run reports only

     # ── Final result ───────────────────────────────────────────────────────
    if errors:
         print(f"ERROR: V1.82.1 validation failed ({len(errors)} errors):\n"
               + "\n".join(f"   - {e}" for e in errors))
         sys.exit(1)

    print(f"SUCCESS: V1.82.1 VALIDATED (Cross-file alignment OK).")


if __name__ == "__main__":
    main()
