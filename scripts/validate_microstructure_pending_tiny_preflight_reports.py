import argparse
import json
from pathlib import Path
import sys

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    v_norm = args.version.replace(".", "_").lower()
    root = Path(__file__).parent.parent
    reports_dir = root / "reports/research"

    summary_p = reports_dir / f"microstructure_pending_tiny_preflight_summary_{v_norm}.json"
    state_p = root / "reports/PROJECT_STATE.json"
    metrics_p = root / "reports/current/latest_metrics.json"
    rec_p = reports_dir / f"{v_norm}_recommendation.json"

    files = [summary_p, state_p, metrics_p, rec_p]
    data = []
    for f in files:
        if not f.exists():
            print(f"ERROR: Missing file {f}")
            sys.exit(1)
        try:
            with open(f) as j:
                content = j.read()
                # Forbidden terms in JSON values (as strings)
                forbidden_terms = ["NaN", "Infinity"]
                for term in forbidden_terms:
                    if f": {term}" in content or f": {term}," in content:
                        print(f"ERROR: Forbidden term '{term}' found in {f}")
                        sys.exit(1)
                
                parsed = json.loads(content)
                data.append(parsed)
        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to parse {f}: {e}")
            sys.exit(1)

    summary, state, metrics, rec = data

    # 1. Alignment checks
    fields = [
        "final_verdict", "recommended_next_step", "next_allowed_phase",
        "pending_human_approval_mode_ready", "tiny_network_preflight_command_prepared",
        "tiny_network_preflight_runner_blocked_without_approval",
        "human_approval_granted", "approval_phrase_validated", "approval_phrase_not_provided"
    ]

    for field in fields:
        val = summary.get(field)
        if state.get(field) != val or metrics.get(field) != val or rec.get(field) != val:
            print(f"ERROR: Field mismatch for '{field}'")
            print(f"Summary: {summary.get(field)}")
            print(f"State: {state.get(field)}")
            print(f"Metrics: {metrics.get(field)}")
            print(f"Rec: {rec.get(field)}")
            sys.exit(1)

    if summary.get("verdict_alignment_status") != "PENDING_TINY_PREFLIGHT_VERDICT_ALIGNED":
        print(f"ERROR: verdict_alignment_status incorrect: {summary.get('verdict_alignment_status')}")
        sys.exit(1)

    # 2. Safety & Hardening checks
    expected_bools = {
        "human_approval_granted": False,
        "approval_phrase_provided": False,
        "approval_phrase_not_provided": True,
        "approval_phrase_validated": False,
        "approval_phrase_required": True,
        "pending_human_approval_mode": True,
        "pending_human_approval_mode_ready": True,
        "tiny_network_preflight_command_prepared": True,
        "tiny_network_preflight_command_executed": False,
        "tiny_network_preflight_runner_blocked_without_approval": True,
        "blocked_runner_test_passed": True,
        "no_network_runtime_assertions_passed": True,
        "no_write_runtime_assertions_passed": True,
        "future_execution_protocol_defined": True,
        "network_enabled": False,
        "network_disabled": True,
        "future_network_activation_requires_separate_approval": True,
        "external_api_called": False,
        "external_data_downloaded": False,
        "tiny_network_collection_executed": False,
        "controlled_collection_executed": False,
        "real_collection_executed": False,
        "real_collection_approved": False,
        "new_data_files_created": False,
        "no_data_directory_writes": True,
        "data_directory_writes_allowed": False,
        "parquet_created": False,
        "csv_created": False,
        "sqlite_created": False,
        "jsonl_created": False,
        "db_created": False,
        "trading_allowed": False,
        "strategy_link_allowed": False,
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "codex_cli_called": False,
        "real_orders_possible": False,
        "validator_hardened": True,
        "negative_tests_added": True,
        "negative_tests_passed": True,
        "portable_tests_passed": True,
        "absolute_paths_removed_from_tests": True,
        "absolute_paths_removed_from_repo": True,
        "external_validation_hardened": True,
        "machine_specific_paths_scan_passed": True,
        "audit_zip_version_inference_fixed": True,
        "audit_zip_infers_v1_69_5": True,
        "audit_zip_no_v1_12_2_fallback": True,
        "validator_passes_in_clean_extraction": True,
        "audit_passes_in_clean_extraction": True,
        "smoke_passes_in_clean_extraction": True,
        "path_portability_hardened": True,
        "reports_grep_results_removed": True,
        "report_index_paths_are_relative": True,
        "smoke_reports_paths_are_portable": True,
        "release_reports_paths_are_portable": True,
        "audit_reports_paths_are_portable": True,
        "structure_hardened": True,
        "expected_modules_present": True,
        "package_init_present": True,
        "release_report_final": True,
        "preliminary_release_report_absent": True
    }

    for k, v in expected_bools.items():
        if summary.get(k) is not v:
            print(f"ERROR: Hardening check failed: {k} must be {v}, got {summary.get(k)}")
            sys.exit(1)

    # V1.69.5 validation
    if summary.get("path_portability_hardened") != True:
        print("ERROR: path_portability_hardened must be True")
        sys.exit(1)
    if summary.get("scanned_patterns_redacted") != True:
        print("ERROR: scanned_patterns_redacted must be True")
        sys.exit(1)
    if summary.get("machine_specific_paths_scan_command_label") != "MACHINE_SPECIFIC_PATH_SCAN_REDACTED":
        print("ERROR: machine_specific_paths_scan_command_label mismatch")
        sys.exit(1)
    if summary.get("audit_zip_infers_v1_69_5") != True:
        print("ERROR: audit_zip_infers_v1_69_5 must be True")
        sys.exit(1)
    if summary.get("audit_zip_no_v1_12_2_fallback") != True:
        print("ERROR: audit_zip_no_v1_12_2_fallback must be True")
        sys.exit(1)

    # 3. Forbidden Terms & Verdict alignment
    forbidden_verdict_terms = ["VALIDATED", "APPROVAL_GRANTED", "APPROVAL_ACCEPTED", "NETWORK_ENABLED", "REAL_COLLECTION_APPROVED", "REAL_COLLECTION_EXECUTED"]
    verdict = summary.get("final_verdict", "")
    for term in forbidden_verdict_terms:
        if term in verdict:
            print(f"ERROR: Forbidden term '{term}' found in final_verdict: {verdict}")
            sys.exit(1)

    forbidden_rec_terms = ["enable network now", "approval granted", "approval phrase accepted", "real collection approved", "paper live", "real trading", "preregistration"]
    rec_step = summary.get("recommended_next_step", "")
    for term in forbidden_rec_terms:
        if term in rec_step.lower():
            print(f"ERROR: Forbidden term '{term}' found in recommended_next_step: {rec_step}")
            sys.exit(1)

    # 4. Portability checks (Machine-specific paths)
    forbidden_paths = ["/Users/" + "lilianserre", "/mnt/" + "data"]
    # Scan tests specifically
    test_files = list((root / "tests/research").glob("test_microstructure_pending_tiny_preflight_v1_69_*.py"))
    for tf in test_files:
        with open(tf) as f:
            content = f.read()
            for path in forbidden_paths:
                if path in content:
                    print(f"ERROR: Machine-specific path '{path}' found in test file {tf}")
                    sys.exit(1)
    
    # Scan a few critical scripts
    critical_scripts = ["scripts/audit_clean_zip.py", "scripts/release_clean_zip.py", "scripts/smoke_test_clean_zip.py"]
    for cs in critical_scripts:
        cs_p = root / cs
        if cs_p.exists():
            with open(cs_p) as f:
                content = f.read()
                for path in forbidden_paths:
                    if path in content:
                        print(f"ERROR: Machine-specific path '{path}' found in script {cs}")
                        sys.exit(1)

    # 4b. Additional V1.69.4 Portability checks
    grep_results_p = root / "reports/grep_results.txt"
    if grep_results_p.exists():
        print("ERROR: reports/grep_results.txt must be removed")
        sys.exit(1)

    report_index_p = root / "reports/REPORT_INDEX.md"
    if report_index_p.exists():
        with open(report_index_p) as f:
            content = f.read()
            if "file:///Users/" in content:
                print("ERROR: REPORT_INDEX.md contains absolute file:///Users/ paths")
                sys.exit(1)

    latest_summary_p = root / "reports/current/latest_summary.md"
    if latest_summary_p.exists():
        with open(latest_summary_p) as f:
            content = f.read()
            for path in forbidden_paths:
                if path in content:
                    print(f"ERROR: Machine-specific path '{path}' found in latest_summary.md")
                    sys.exit(1)

    smoke_v_norm = args.version.replace(".", "_").lower()
    for ext in [".json", ".md"]:
        smoke_p = root / f"reports/zip_smoke_test_{smoke_v_norm}{ext}"
        if smoke_p.exists():
            with open(smoke_p) as f:
                content = f.read()
                for path in forbidden_paths:
                    if path in content:
                        print(f"ERROR: Machine-specific path '{path}' found in {smoke_p.name}")
                        sys.exit(1)
        
        release_p = root / f"reports/release_zip_{smoke_v_norm}{ext}"
        if release_p.exists():
            with open(release_p) as f:
                content = f.read()
                for path in forbidden_paths:
                    if path in content:
                        print(f"ERROR: Machine-specific path '{path}' found in {release_p.name}")
                        sys.exit(1)

        audit_p = root / f"reports/zip_audit_{smoke_v_norm}{ext}"
        if audit_p.exists():
            with open(audit_p) as f:
                content = f.read()
                for path in forbidden_paths:
                    if path in content:
                        print(f"ERROR: Machine-specific path '{path}' found in {audit_p.name}")
                        sys.exit(1)

    # 4c. Final raw path cleanup check (V1.69.5)
    portability_report_p = root / f"reports/research/microstructure_pending_tiny_preflight_path_portability_audit_{smoke_v_norm}.json"
    if portability_report_p.exists():
        with open(portability_report_p) as f:
            port_data = json.load(f)
            if "machine_specific_paths_scan_command" in port_data:
                 cmd_str = port_data["machine_specific_paths_scan_command"]
                 for path in forbidden_paths:
                     if path in cmd_str:
                         print(f"ERROR: Forbidden path '{path}' found in scan command in {portability_report_p.name}")
                         sys.exit(1)
            if port_data.get("machine_specific_paths_scan_command_label") != "MACHINE_SPECIFIC_PATH_SCAN_REDACTED":
                 print(f"ERROR: machine_specific_paths_scan_command_label mismatch in {portability_report_p.name}")
                 sys.exit(1)
            if not port_data.get("scanned_patterns_redacted"):
                 print(f"ERROR: scanned_patterns_redacted must be True in {portability_report_p.name}")
                 sys.exit(1)

    if verdict != "MICROSTRUCTURE_TINY_NETWORK_PREFLIGHT_COMMAND_PREPARED_PENDING_APPROVAL":
        print(f"ERROR: final_verdict mismatch: {verdict}")
        sys.exit(1)

    if summary.get("next_allowed_phase") != "provide_explicit_human_approval_phrase_for_one_request_preflight":
        print(f"ERROR: next_allowed_phase mismatch: {summary.get('next_allowed_phase')}")
        sys.exit(1)

    req_phrase = "I explicitly approve a one-request tiny network preflight with no data directory writes and no trading."
    if summary.get("required_approval_phrase") != req_phrase:
        print(f"ERROR: required_approval_phrase mismatch. Expected: {req_phrase}")
        sys.exit(1)

    # 5. Reports presence
    required_stems = [
        "microstructure_pending_tiny_preflight_input_guard",
        "microstructure_approval_phrase_gate",
        "microstructure_pending_approval_mode",
        "microstructure_tiny_preflight_command_builder",
        "microstructure_blocked_runner",
        "microstructure_no_network_runtime_assertions",
        "microstructure_no_write_runtime_assertions",
        "microstructure_future_execution_protocol",
        "microstructure_pending_tiny_preflight_structure_audit",
        "microstructure_pending_tiny_preflight_negative_tests",
        "microstructure_pending_tiny_preflight_validator_hardening",
        "microstructure_pending_tiny_preflight_external_validation_audit",
        "microstructure_pending_tiny_preflight_path_portability_audit",
        "microstructure_pending_tiny_preflight_decision",
        "microstructure_pending_tiny_preflight_recommendation",
        "microstructure_pending_tiny_preflight_summary",
        "microstructure_pending_tiny_preflight_consistency_check"
    ]
    for stem in required_stems:
        if not (reports_dir / f"{stem}_{v_norm}.json").exists():
            print(f"ERROR: Missing report {stem}_{v_norm}.json")
            sys.exit(1)
        if not (reports_dir / f"{stem}_{v_norm}.md").exists():
            print(f"ERROR: Missing report {stem}_{v_norm}.md")
            sys.exit(1)

    doc_p = root / f"docs/microstructure_pending_tiny_preflight_{v_norm}.md"
    if not doc_p.exists():
        print(f"ERROR: Missing final doc {doc_p}")
        sys.exit(1)

    # 6. Release report check (V1.69.3 must be final)
    rel_p = reports_dir / f"release_zip_{v_norm}.json"
    if rel_p.exists():
        with open(rel_p) as f:
            rel = json.load(f)
            if rel.get("release_ready_for_external_review") is not True:
                print(f"ERROR: release_ready_for_external_review must be True in {rel_p}")
                sys.exit(1)
            if "Preliminary" in str(rel.get("blocking_reason", "")):
                print(f"ERROR: Release report is still preliminary: {rel_p}")
                sys.exit(1)

    # 7. Consistency check specifics
    const_p = reports_dir / f"microstructure_pending_tiny_preflight_consistency_check_{v_norm}.json"
    with open(const_p) as f:
        const = json.load(f)
    if const.get("version") != args.version.upper():
        print(f"ERROR: Consistency check version mismatch: {const.get('version')}")
        sys.exit(1)
    
    v_low = args.version.lower()
    if v_low == "v1.69.5":
        expected_prev = "V1.69.4"
    elif v_low == "v1.69.4":
        expected_prev = "V1.69.3"
    elif v_low == "v1.69.3":
        expected_prev = "V1.69.2"
    else:
        expected_prev = "V1.69.1"

    if const.get("previous_base") != expected_prev:
        print(f"ERROR: Consistency check previous_base mismatch: {const.get('previous_base')}")
        sys.exit(1)
    if const.get("issues") != []:
        print(f"ERROR: Consistency check has issues: {const.get('issues')}")
        sys.exit(1)
    if const.get("consistency_check_status") != "MICROSTRUCTURE_PENDING_TINY_PREFLIGHT_REPORTS_CONSISTENT_INFRASTRUCTURE_ONLY":
        print(f"ERROR: consistency_check_status incorrect: {const.get('consistency_check_status')}")
        sys.exit(1)

    print(f"SUCCESS: V1.69.1 hardened reports validated for {args.version}")

if __name__ == "__main__":
    main()
