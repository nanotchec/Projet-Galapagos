from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path


def validate_reports(version: str):
    v_norm = version.lower().replace(".", "_")
    reports_dir = Path("reports/research")
    
    required_reports = [
        "microstructure_adapter_fixture_input_guard",
        "microstructure_fixture_inventory",
        "microstructure_fixture_loader_audit",
        "microstructure_adapter_field_mapping",
        "microstructure_timestamp_normalization",
        "microstructure_normalized_record_schema",
        "microstructure_fixture_manifest_validation",
        "microstructure_network_disabled_fixture_tests",
        "microstructure_adapter_refinement_audit",
        "microstructure_fixture_validation_audit",
        "microstructure_adapter_fixture_test_results",
        "microstructure_adapter_fixture_recommendation",
        "microstructure_adapter_fixture_summary",
        "microstructure_adapter_fixture_consistency_check",
        f"{v_norm}_recommendation"
    ]
    
    errors = []
    
    # 1. Master State Checks
    project_state_path = Path("reports/PROJECT_STATE.json")
    if not project_state_path.exists():
        errors.append("Missing PROJECT_STATE.json")
    else:
        with open(project_state_path) as f:
            ps = json.load(f)
            if ps.get("version") != version:
                errors.append(f"PROJECT_STATE version mismatch: {ps.get('version')} != {version}")
            if ps.get("current_version") != version:
                errors.append(f"PROJECT_STATE current_version mismatch: {ps.get('current_version')} != {version}")
            if ps.get("previous_version") != "V1.55.2":
                errors.append(f"PROJECT_STATE previous_version mismatch: {ps.get('previous_version')} != V1.55.2")
            if ps.get("previous_base") != "V1.55.2":
                errors.append(f"PROJECT_STATE previous_base mismatch: {ps.get('previous_base')} != V1.55.2")
            
            # Alignment fields
            alignment_fields = [
                "latest_current_version_aligned",
                "latest_previous_version_aligned",
                "latest_previous_base_aligned",
                "project_state_current_version_aligned",
                "release_ready_consistent",
                "project_state_aligned",
                "latest_metrics_aligned",
                "latest_summary_aligned",
                "docs_final_present",
                "docs_final_version_aligned"
            ]
            for field in alignment_fields:
                if ps.get(field) is not True:
                    errors.append(f"PROJECT_STATE {field} must be True")

            if ps.get("docs_version_alignment_status") != "DOCS_VERSION_ALIGNED":
                errors.append("PROJECT_STATE docs_version_alignment_status must be DOCS_VERSION_ALIGNED")
            
            expected_doc_path = f"docs/microstructure_adapter_fixture_tests_{v_norm}.md"
            if ps.get("docs_final_path") != expected_doc_path:
                errors.append(f"PROJECT_STATE docs_final_path mismatch: {ps.get('docs_final_path')} != {expected_doc_path}")

            if ps.get("release_ready_for_external_review") is not True:
                errors.append("PROJECT_STATE release_ready_for_external_review must be True")

    latest_metrics_path = Path("reports/current/latest_metrics.json")
    if not latest_metrics_path.exists():
        errors.append("Missing latest_metrics.json")
    else:
        with open(latest_metrics_path) as f:
            lm = json.load(f)
            if lm.get("version") != version:
                errors.append(f"latest_metrics version mismatch: {lm.get('version')} != {version}")
            if lm.get("current_version") != version:
                errors.append(f"latest_metrics current_version mismatch: {lm.get('current_version')} != {version}")
            if lm.get("previous_version") != "V1.55.2":
                errors.append(f"latest_metrics previous_version mismatch: {lm.get('previous_version')} != V1.55.2")
            if lm.get("previous_base") != "V1.55.2":
                errors.append(f"latest_metrics previous_base mismatch: {lm.get('previous_base')} != V1.55.2")
            
            # Alignment fields
            for field in [
                "latest_current_version_aligned",
                "latest_previous_version_aligned",
                "latest_previous_base_aligned",
                "release_ready_consistent",
                "docs_final_present",
                "docs_final_version_aligned"
            ]:
                if lm.get(field) is not True:
                    errors.append(f"latest_metrics {field} must be True")

            if lm.get("docs_version_alignment_status") != "DOCS_VERSION_ALIGNED":
                errors.append("latest_metrics docs_version_alignment_status must be DOCS_VERSION_ALIGNED")

            if lm.get("release_ready_consistent") is not True:
                errors.append("latest_metrics release_ready_consistent must be True")

    # 1b. Documentation Check
    doc_path = Path(f"docs/microstructure_adapter_fixture_tests_{v_norm}.md")
    if not doc_path.exists():
        errors.append(f"Missing documentation file: {doc_path}")
    else:
        with open(doc_path) as f:
            doc_content = f.read()
            if version not in doc_content:
                errors.append(f"Documentation {doc_path} does not mention version {version}")
            
            forbidden_words = [
                "strategy validated",
                "paper live ready",
                "real trading ready",
                "preregistration ready"
            ]
            for word in forbidden_words:
                if word in doc_content.lower():
                    errors.append(f"Documentation {doc_path} contains forbidden wording: '{word}'")

    # 2. Individual Reports Checks
    for report in required_reports:
        base_name = report
        if v_norm not in base_name and report != f"{v_norm}_recommendation":
            base_name = f"{base_name}_{v_norm}"
            
        json_path = reports_dir / f"{base_name}.json"
        md_path = reports_dir / f"{base_name}.md"
        
        if not json_path.exists():
            errors.append(f"Missing JSON report: {json_path}")
            continue
            
        if not md_path.exists():
            errors.append(f"Missing MD report: {md_path}")
            
        try:
            with open(json_path) as f:
                data = json.load(f)
                
                # Check version and base in report
                if data.get("version") != version:
                    errors.append(f"Version mismatch in {json_path}: {data.get('version')}")
                if data.get("previous_base") != "V1.55.2":
                    errors.append(f"previous_base mismatch in {json_path}: {data.get('previous_base')}")

                # Check finiteness
                dumped = json.dumps(data)
                if "NaN" in dumped or "Infinity" in dumped:
                    errors.append(f"Finiteness issue (NaN/Infinity) in {json_path}")
                
                # Safety flags and scientific conclusion maintenance
                if report == "microstructure_adapter_fixture_summary":
                    required_flags = {
                        "network_disabled": True,
                        "dry_run_only": True,
                        "local_fixture_only": True,
                        "fixture_only": True,
                        "synthetic_or_minimal_sample": True,
                        "not_for_research_results": True,
                        "real_collection_executed": False,
                        "external_data_downloaded": False,
                        "external_api_called": False,
                        "new_data_files_created": False,
                        "no_data_directory_writes": True,
                        "parquet_created": False,
                        "csv_created": False,
                        "sqlite_created": False,
                        "requests_executed_count": 0,
                        "data_path_rejected": True,
                        "no_new_filter": True,
                        "no_strategy_validated": True,
                        "no_preregistration_yet": True,
                        "no_paper_live": True,
                        "no_real_trading": True,
                        "holdout_executed": False,
                        "codex_cli_called": False,
                        "real_orders_possible": False,
                        "final_verdict": "MICROSTRUCTURE_ADAPTER_FIXTURE_TESTS_READY",
                        "docs_version_alignment_status": "DOCS_VERSION_ALIGNED",
                        "docs_final_present": True
                    }
                    for flag, val in required_flags.items():
                        if data.get(flag) != val:
                            errors.append(f"Summary flag mismatch: {flag} should be {val}, got {data.get(flag)}")
                    
                if report == "microstructure_adapter_fixture_consistency_check":
                    if data.get("consistency_check_status") != "MICROSTRUCTURE_ADAPTER_FIXTURE_REPORTS_CONSISTENT_INFRASTRUCTURE_ONLY":
                        errors.append("Incorrect consistency_check_status")
                    if data.get("issues") != []:
                        errors.append("consistency_check issues must be empty")
                    
                    # Alignment check
                    for alignment_field in [
                        "latest_current_version_aligned",
                        "latest_previous_version_aligned",
                        "latest_previous_base_aligned",
                        "project_state_current_version_aligned",
                        "release_ready_consistent",
                        "docs_final_present",
                        "docs_final_version_aligned"
                    ]:
                        if data.get(alignment_field) is not True:
                            errors.append(f"Consistency check {alignment_field} must be True")
                    
                    if data.get("docs_version_alignment_status") != "DOCS_VERSION_ALIGNED":
                        errors.append("Consistency check docs_version_alignment_status must be DOCS_VERSION_ALIGNED")

        except Exception as e:
            errors.append(f"Failed to parse {json_path}: {e}")

    # 3. Forbidden Files Check
    forbidden_extensions = [".parquet", ".csv", ".sqlite", ".db", ".jsonl"]
    data_dir = Path("data")
    now = time.time()
    if data_dir.exists():
        for p in data_dir.rglob("*"):
            if p.suffix in forbidden_extensions:
                if p.stat().st_mtime > (now - 600):
                    errors.append(f"RECENTLY CREATED/MODIFIED Forbidden file found in data/: {p}")
            if p.is_file() and "fixtures" not in str(p):
                 # No files should be in data/ if we are fixture_only and no_data_directory_writes
                 if p.stat().st_mtime > (now - 600):
                     errors.append(f"Forbidden new file in data/: {p}")

    # 4. Release Report Check
    release_report_path = Path(f"reports/release_zip_{v_norm}.json")
    if release_report_path.exists():
        with open(release_report_path) as f:
            rr = json.load(f)
            checks = ["final_audit_passed", "final_smoke_passed", "final_consistency_passed"]
            all_green = all(rr.get(c) is True for c in checks)
            if all_green:
                 if rr.get("release_ready_for_external_review") is not True:
                     errors.append("release_ready_for_external_review must be True when all checks pass")
                 if rr.get("release_ready_consistent") is not True:
                     errors.append("release_ready_consistent must be True in release report when all checks pass")
            else:
                 if rr.get("release_ready_for_external_review") is True:
                     errors.append("release_ready_for_external_review must be False if checks fail")
                 if not rr.get("issues") and not rr.get("blocking_reason"):
                     errors.append("release_report must have issues or blocking_reason if release_ready is False")

    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        sys.exit(1)
    else:
        print(f"{version} validation passed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    validate_reports(args.version)
