import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    version = args.version.upper()
    v_norm = version.lower().replace(".", "_")
    reports_dir = Path("reports/research")

    required_reports = [
        f"microstructure_backfill_input_guard_{v_norm}",
        f"microstructure_source_adapter_contract_{v_norm}",
        f"microstructure_backfill_request_plan_{v_norm}",
        f"microstructure_dry_run_schedule_{v_norm}",
        f"microstructure_manifest_schema_{v_norm}",
        f"microstructure_expected_file_layout_{v_norm}",
        f"microstructure_causal_timestamp_policy_{v_norm}",
        f"microstructure_collection_safety_guard_{v_norm}",
        f"microstructure_post_collection_qc_plan_{v_norm}",
        f"microstructure_data_contract_alignment_{v_norm}",
        f"microstructure_dry_run_audit_{v_norm}",
        f"microstructure_backfill_recommendation_{v_norm}",
        f"microstructure_backfill_dryrun_summary_{v_norm}",
        f"microstructure_backfill_dryrun_consistency_check_{v_norm}",
        f"{v_norm}_recommendation"
    ]

    for base in required_reports:
        j_path = reports_dir / f"{base}.json"
        m_path = reports_dir / f"{base}.md"
        if not j_path.exists():
            print(f"ERROR: Missing JSON {j_path}")
            sys.exit(1)
        if not m_path.exists():
            print(f"ERROR: Missing MD {m_path}")
            sys.exit(1)

        with open(j_path) as f:
            text = f.read()
            if "NaN" in text or "Infinity" in text:
                print(f"ERROR: Finiteness issue in {j_path}")
                sys.exit(1)

    # Check for invalid JSON files locally
    invalid_json_files = []
    for f in reports_dir.glob("*.json"):
        try:
            with open(f) as fp:
                json.load(fp)
        except json.JSONDecodeError:
            invalid_json_files.append(f.name)
            
    if invalid_json_files:
        print(f"ERROR: Invalid JSON files found locally: {invalid_json_files}")
        sys.exit(1)

    # Global State Alignment Checks
    with open("reports/PROJECT_STATE.json") as f:
        ps = json.load(f)
    with open("reports/current/latest_metrics.json") as f:
        lm = json.load(f)
    with open("reports/current/latest_summary.md") as f:
        ls_content = f.read()

    target_v = "V1.53.2"
    target_prev = "V1.53.1"

    if ps.get("version") != target_v:
        print(f"ERROR: PROJECT_STATE version mismatch: {ps.get('version')} != {target_v}")
        sys.exit(1)
    if ps.get("current_version") != target_v:
        print(f"ERROR: PROJECT_STATE current_version mismatch: {ps.get('current_version')} != {target_v}")
        sys.exit(1)
    if ps.get("previous_version") != target_prev:
        print(f"ERROR: PROJECT_STATE previous_version mismatch: {ps.get('previous_version')} != {target_prev}")
        sys.exit(1)
    if ps.get("previous_base") != target_prev:
        print(f"ERROR: PROJECT_STATE previous_base mismatch: {ps.get('previous_base')} != {target_prev}")
        sys.exit(1)

    if lm.get("version") != target_v:
        print(f"ERROR: latest_metrics version mismatch: {lm.get('version')} != {target_v}")
        sys.exit(1)
    if lm.get("current_version") != target_v:
        print(f"ERROR: latest_metrics current_version mismatch: {lm.get('current_version')} != {target_v}")
        sys.exit(1)
    if lm.get("previous_version") != target_prev:
        print(f"ERROR: latest_metrics previous_version mismatch: {lm.get('previous_version')} != {target_prev}")
        sys.exit(1)
    if lm.get("previous_base") != target_prev:
        print(f"ERROR: latest_metrics previous_base mismatch: {lm.get('previous_base')} != {target_prev}")
        sys.exit(1)

    if target_v not in ls_content:
        print(f"ERROR: latest_summary.md does not mention {target_v}")
        sys.exit(1)

    if not ps.get("project_state_version_aligned"):
        print("ERROR: project_state_version_aligned is not true")
        sys.exit(1)
    if not ps.get("latest_metrics_version_aligned"):
        print("ERROR: latest_metrics_version_aligned is not true")
        sys.exit(1)
    if not ps.get("latest_summary_version_aligned"):
        print("ERROR: latest_summary_version_aligned is not true")
        sys.exit(1)

    cc_path = reports_dir / f"microstructure_backfill_dryrun_consistency_check_{v_norm}.json"
    with open(cc_path) as f:
        cc = json.load(f)

    if cc.get("version") != target_v:
        print(f"ERROR: cc version != {target_v}")
        sys.exit(1)
    if cc.get("previous_base") != target_prev:
        print(f"ERROR: cc previous_base != {target_prev}")
        sys.exit(1)
    if not cc.get("all_json_files_parseable"):
        print("ERROR: all_json_files_parseable != true")
        sys.exit(1)
    if cc.get("invalid_json_files") != []:
        print("ERROR: invalid_json_files != []")
        sys.exit(1)
    if not cc.get("legacy_invalid_json_removed"):
        print("ERROR: legacy_invalid_json_removed != true")
        sys.exit(1)

    if cc.get("issues") != []:
        print("ERROR: cc issues != []")
        sys.exit(1)
    if cc.get("consistency_check_status") != "MICROSTRUCTURE_BACKFILL_DRYRUN_REPORTS_CONSISTENT_INFRASTRUCTURE_ONLY":
        print("ERROR: cc status incorrect")
        sys.exit(1)

    # Boolean flags
    flags = {
        "required_reports_present": True,
        "required_markdown_reports_present": True,
        "project_state_aligned": True,
        "latest_metrics_aligned": True,
        "latest_summary_aligned": True,
        "dry_run_only": True,
        "real_collection_executed": False,
        "external_data_downloaded": False,
        "external_api_called": False,
        "new_data_files_created": False,
        "parquet_created": False,
        "csv_created": False,
        "sqlite_created": False,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "codex_cli_called": False,
        "real_orders_possible": False
    }

    for k, v in flags.items():
        if cc.get(k) is not v:
            print(f"ERROR: {k} is {cc.get(k)} expected {v}")
            sys.exit(1)

    if "VALIDATED" in cc.get("final_verdict", ""):
        print("ERROR: final_verdict contains VALIDATED")
        sys.exit(1)

    next_step = cc.get("recommended_next_step", "").lower()
    if "paper live" in next_step or "real trading" in next_step or "preregistration" in next_step:
        print("ERROR: next step implies paper live, real trading or preregistration")
        sys.exit(1)

    # Project state check
    with open("reports/PROJECT_STATE.json") as f:
        ps = json.load(f)
    if "consistency_check_status" not in ps:
        print("ERROR: PROJECT_STATE missing consistency_check_status")
        sys.exit(1)

    with open("reports/current/latest_metrics.json") as f:
        lm = json.load(f)
    if "consistency_check_status" not in lm:
        print("ERROR: latest_metrics missing consistency_check_status")
        sys.exit(1)

    if ps.get("version") != lm.get("version"):
        print("ERROR: PROJECT_STATE version != latest_metrics version")
        sys.exit(1)

    print("V1.53 validation passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
