import argparse
import sys
import json
import hashlib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

for path in (PROJECT_ROOT, SRC_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

CRITICAL_CROSS_FILE_FIELDS = [
  "version",
  "final_verdict",
  "approval_source_verified",
  "human_approval_granted",
  "v1_87_authorized",
  "extension_materialization_executed",
  "tiny_extension_only",
  "full_dataset_created",
  "network_executed",
  "new_network_requests_executed",
  "data_directory_writes_allowed",
  "data_write_approved",
  "data_directory_write_attempted",
  "new_data_files_created",
  "extension_actual_write_executed",
  "unapproved_data_write_detected",
  "total_new_data_files_created",
  "created_files_count",
  "total_data_bytes_written",
  "existing_v1_84_files_modified",
  "v1_84_manifest_modified",
  "v1_84_schema_snapshot_modified",
  "v1_84_preview_records_modified",
  "parquet_created",
  "csv_created",
  "sqlite_created",
  "jsonl_created",
  "db_created",
  "dataset_created",
  "research_dataset_updated",
  "trading_allowed",
  "real_orders_possible",
  "no_real_trading",
  "no_paper_live",
  "ml_signal_validation_executed",
  "predictions_created",
  "labels_created",
  "targets_created",
  "pytest_executed",
  "pytest_exit_code",
  "pytest_failed_count",
  "release_zip_created",
  "release_ready_for_external_review",
  "clean_zip_ready_for_external_review",
  "smoke_test_passed",
  "blocking_reason"
]

def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    if args.version != "v1_87_2":
        print(f"Error: Version {args.version} not supported.")
        sys.exit(1)

    try:
        # Mandatory files
        required_paths = {
            "summary": PROJECT_ROOT / "reports/research/microstructure_data_contract_extension_materialization_summary_v1_87_2.json",
            "file_audit": PROJECT_ROOT / "reports/research/microstructure_data_contract_extension_materialization_file_audit_v1_87_2.json",
            "safety_check": PROJECT_ROOT / "reports/research/microstructure_data_contract_extension_materialization_safety_check_v1_87_2.json",
            "consistency_check": PROJECT_ROOT / "reports/research/microstructure_data_contract_extension_materialization_consistency_check_v1_87_2.json",
            "metrics": PROJECT_ROOT / "reports/current/latest_metrics.json",
            "project_state": PROJECT_ROOT / "reports/PROJECT_STATE.json",
            "latest_summary": PROJECT_ROOT / "reports/current/latest_summary.md",
            "report_index": PROJECT_ROOT / "reports/REPORT_INDEX.md",
            "release_zip": PROJECT_ROOT / "reports/release_zip_v1_87_2.json",
            "zip_audit": PROJECT_ROOT / "reports/zip_audit_v1_87_2.json",
            "zip_smoke": PROJECT_ROOT / "reports/zip_smoke_test_v1_87_2.json",
            "code_review_doc": PROJECT_ROOT / "docs/code_review_v1_87_2.md",
            "materialization_doc": PROJECT_ROOT / "docs/microstructure_data_contract_extension_materialization_v1_87_2.md"
        }

        for name, p in required_paths.items():
            if not p.exists():
                print(f"Validation FAILED: Mandatory file {name} missing at {p}")
                sys.exit(1)

        with open(required_paths["summary"], "r") as f: summary_data = json.load(f)
        with open(required_paths["metrics"], "r") as f: metrics_data = json.load(f)
        with open(required_paths["project_state"], "r") as f: project_state = json.load(f)
        with open(required_paths["file_audit"], "r") as f: file_audit = json.load(f)
        with open(required_paths["release_zip"], "r") as f: release_zip = json.load(f)
        with open(required_paths["zip_audit"], "r") as f: zip_audit = json.load(f)
        with open(required_paths["zip_smoke"], "r") as f: zip_smoke = json.load(f)

        # 1. Strict Negative/Positive Checks on Summary
        must_be_true = [
            "release_ready_for_external_review",
            "clean_zip_ready_for_external_review",
            "smoke_test_passed",
            "docs_code_review_present",
            "materialization_doc_present"
        ]
        must_be_false = [
            "network_executed",
            "dataset_created",
            "research_dataset_updated",
            "full_dataset_created",
            "real_orders_possible",
            "trading_allowed",
            "ml_signal_validation_executed",
            "unapproved_data_write_detected",
            "existing_v1_84_files_modified",
            "v1_84_manifest_modified",
            "v1_84_schema_snapshot_modified",
            "v1_84_preview_records_modified",
            "parquet_created",
            "csv_created",
            "sqlite_created",
            "jsonl_created",
            "db_created"
        ]
        
        for field in must_be_true:
            if summary_data.get(field) is not True:
                 print(f"Validation FAILED: {field} must be True")
                 sys.exit(1)
                 
        for field in must_be_false:
            if summary_data.get(field) is not False:
                 print(f"Validation FAILED: {field} must be False")
                 sys.exit(1)

        if summary_data.get("blocking_reason") is not None:
            print("Validation FAILED: blocking_reason must be null")
            sys.exit(1)

        if summary_data.get("total_new_data_files_created") > 2:
            print("Validation FAILED: total_new_data_files_created > 2")
            sys.exit(1)

        if summary_data.get("created_files_count") > 2:
            print("Validation FAILED: created_files_count > 2")
            sys.exit(1)

        if summary_data.get("total_data_bytes_written") > 15000:
            print("Validation FAILED: total_data_bytes_written > 15000")
            sys.exit(1)

        # 2. REPORT_INDEX and latest_summary checks
        with open(required_paths["report_index"], "r") as f: report_index_content = f.read()
        if "V1.87.2" not in report_index_content and "v1_87_2" not in report_index_content:
             print("Validation FAILED: REPORT_INDEX.md does not reference V1.87.2")
             sys.exit(1)
             
        with open(required_paths["latest_summary"], "r") as f: latest_summary_content = f.read()
        if "V1.87.2" not in latest_summary_content:
             print("Validation FAILED: latest_summary.md does not mention V1.87.2")
             sys.exit(1)

        # 3. Strict Cross-File Alignment
        for field in CRITICAL_CROSS_FILE_FIELDS:
            if field not in summary_data:
                print(f"Validation FAILED: Field '{field}' missing in summary")
                sys.exit(1)
            if field not in metrics_data:
                print(f"Validation FAILED: Field '{field}' missing in latest_metrics")
                sys.exit(1)
            if field not in project_state:
                print(f"Validation FAILED: Field '{field}' missing in PROJECT_STATE")
                sys.exit(1)
            
            val_summary = summary_data[field]
            val_metrics = metrics_data[field]
            val_state = project_state[field]
            
            if not (val_summary == val_metrics == val_state):
                print(f"Validation FAILED: Field '{field}' diverged: summary={val_summary}, metrics={val_metrics}, state={val_state}")
                sys.exit(1)

        # 4. Strict Release/Smoke/Audit data checks
        if release_zip.get("release_zip_created") is not True or release_zip.get("final_zip_created") is not True:
            print("Validation FAILED: release_zip report indicates zip not created")
            sys.exit(1)
        if release_zip.get("release_ready_for_external_review") is not True or release_zip.get("clean_zip_ready_for_external_review") is not True:
            print("Validation FAILED: release_zip report indicates not ready for external review")
            sys.exit(1)
            
        if zip_smoke.get("smoke_test_passed") is not True or zip_smoke.get("smoke_failed_count") != 0:
            print("Validation FAILED: zip_smoke report indicates smoke test failure")
            sys.exit(1)
        if zip_smoke.get("smoke_passed_count") != zip_smoke.get("smoke_commands_count") or zip_smoke.get("smoke_commands_not_empty") is not True:
            print("Validation FAILED: zip_smoke report command count mismatch or empty")
            sys.exit(1)
            
        if zip_audit.get("clean_zip_ready_for_external_review") is not True or zip_audit.get("audit_zip_project_state_version") != "V1.87.2":
            print("Validation FAILED: zip_audit report indicates audit failure or version mismatch")
            sys.exit(1)

        # 5. Physical V1.87 directory check
        v1_87_dir = PROJECT_ROOT / "data/research/microstructure_contract_materialization/v1_87/"
        if not v1_87_dir.exists():
            print("Validation FAILED: Directory v1_87 does not exist")
            sys.exit(1)
        
        actual_files = [f.name for f in v1_87_dir.iterdir() if f.is_file()]
        expected_files = ["extension_manifest.json", "extension_quality_summary.json"]
        if sorted(actual_files) != sorted(expected_files):
            print(f"Validation FAILED: Unexpected files in v1_87: {actual_files}")
            sys.exit(1)
            
        for f in expected_files:
            try:
                with open(v1_87_dir / f, "r") as fp:
                    json.load(fp)
            except Exception as e:
                print(f"Validation FAILED: {f} is not valid JSON: {e}")
                sys.exit(1)

        # 6. Actual V1.84 Hash Check
        v1_84_dir = PROJECT_ROOT / "data/research/microstructure_contract_materialization/v1_84/"
        expected_hashes = {
            "manifest.json": file_audit["v1_84_manifest_sha256"],
            "schema_snapshot.json": file_audit["v1_84_schema_snapshot_sha256"],
            "preview_records.json": file_audit["v1_84_preview_records_sha256"]
        }
        for fname, expected_hash in expected_hashes.items():
            actual_hash = compute_sha256(v1_84_dir / fname)
            if actual_hash != expected_hash:
                print(f"Validation FAILED: Hash mismatch for V1.84 {fname}: expected {expected_hash}, got {actual_hash}")
                sys.exit(1)

        print("V1.87.2 Validation PASSED successfully.")

    except Exception as e:
        print(f"Error during V1.87.2 validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
