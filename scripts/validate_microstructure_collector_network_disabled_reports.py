from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Validate V1.54 Collector Reports")
    parser.add_argument("--version", default="V1.54")
    args = parser.parse_args()

    version = args.version
    v_norm = version.lower().replace(".", "_")
    reports_dir = Path("reports/research")

    required_reports = [
        "microstructure_collector_input_guard",
        "microstructure_network_guard",
        "microstructure_source_adapter_contract",
        "microstructure_request_builder",
        "microstructure_dry_run_executor",
        "microstructure_manifest_validation",
        "microstructure_file_layout_validation",
        "microstructure_collector_safety_audit",
        "microstructure_integration_test_plan",
        "microstructure_collector_test_results",
        "microstructure_collector_recommendation",
        "microstructure_collector_network_disabled_summary",
        "microstructure_collector_network_disabled_consistency_check",
        "v1_54_recommendation"
    ]

    for report in required_reports:
        j_path = reports_dir / f"{report}_{v_norm}.json"
        m_path = reports_dir / f"{report}_{v_norm}.md"

        if not j_path.exists():
            print(f"ERROR: Missing JSON report: {j_path}")
            sys.exit(1)
        if not m_path.exists():
            print(f"ERROR: Missing MD report: {m_path}")
            sys.exit(1)

        with open(j_path) as f:
            data = json.load(f)
            # Check for NaN/Infinity
            dumped = json.dumps(data)
            if "NaN" in dumped or "Infinity" in dumped:
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

    target_v = "V1.54"
    target_prev = "V1.53.2"

    if ps.get("version") != target_v:
        print(f"ERROR: PROJECT_STATE version mismatch: {ps.get('version')} != {target_v}")
        sys.exit(1)
    if lm.get("version") != target_v:
        print(f"ERROR: latest_metrics version mismatch: {lm.get('version')} != {target_v}")
        sys.exit(1)
    if target_v not in ls_content:
        print(f"ERROR: latest_summary.md does not mention {target_v}")
        sys.exit(1)

    if ps.get("network_disabled") is not True:
        print("ERROR: network_disabled must be true in PROJECT_STATE")
        sys.exit(1)
    if ps.get("requests_executed_count") != 0:
        print("ERROR: requests_executed_count must be 0")
        sys.exit(1)

    cc_path = reports_dir / f"microstructure_collector_network_disabled_consistency_check_{v_norm}.json"
    with open(cc_path) as f:
        cc = json.load(f)

    if cc.get("version") != target_v:
        print(f"ERROR: cc version != {target_v}")
        sys.exit(1)
    if cc.get("previous_base") != target_prev:
        print(f"ERROR: cc previous_base != {target_prev}")
        sys.exit(1)
    if cc.get("issues") != []:
        print("ERROR: cc issues != []")
        sys.exit(1)
    if cc.get("network_disabled") is not True:
        print("ERROR: network_disabled must be true in cc")
        sys.exit(1)

    # Ensure no strategy validated etc.
    verdict = cc.get("final_verdict", "")
    if "VALIDATED" in verdict:
        print("ERROR: verdict cannot contain VALIDATED")
        sys.exit(1)

    print(f"V1.54 validation passed.")


if __name__ == "__main__":
    main()
