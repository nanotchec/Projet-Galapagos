from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.signal_selection.report_models import save_signal_report

def main():
    parser = argparse.ArgumentParser(description="Validate Preregistration Reports")
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    v_norm = args.version.lower().replace(".", "_")
    reports_dir = Path("reports/research")
    
    if args.version in ["v1.26.3", "v1.26.4", "v1.26.5", "v1.26.6"]:
        required_stems = [
            f"preregistered_signal_validation_protocol_{v_norm}",
            f"frozen_filter_definition_{v_norm}",
            f"preregistered_protocol_completeness_audit_{v_norm}",
            f"{v_norm}_recommendation"
        ]
        if args.version == "v1.26.6":
            required_stems.append(f"preregistration_archive_integrity_{v_norm}")
    else:
        required_stems = [
            f"preregistered_signal_validation_protocol_{v_norm}",
            f"preregistered_success_criteria_{v_norm}",
            f"preregistered_evidence_classification_{v_norm}",
            f"preregistered_retrospective_check_{v_norm}",
            f"preregistered_future_validation_plan_{v_norm}",
            f"{v_norm}_recommendation"
        ]
    
    issues = []
    loaded_reports = {}
    
    # 1. Existence check
    for stem in required_stems:
        json_path = reports_dir / f"{stem}.json"
        if not json_path.exists():
            issues.append(f"Missing required report: {json_path}")
            continue
        with open(json_path) as f:
            loaded_reports[stem] = json.load(f)

    # 2. Content check if files exist
    if not issues:
        # Check protocol version
        protocol_key = f"preregistered_signal_validation_protocol_{v_norm}"
        protocol = loaded_reports[protocol_key]
        if protocol.get("protocol_version").lower() != args.version.lower():
            issues.append(f"Protocol version mismatch: {protocol.get('protocol_version')} != {args.version}")
            
        if not protocol.get("protocol_locked"):
            issues.append("Protocol not locked")
            
        if args.version == "v1.26.3":
            if not protocol.get("frozen_filter_definition_complete"):
                issues.append("Frozen filter definition not marked complete in protocol")
            
            audit = loaded_reports[f"preregistered_protocol_completeness_audit_{v_norm}"]
            if audit.get("status") != "PREREGISTRATION_PROTOCOL_COMPLETE":
                issues.append(f"Completeness audit failed: {audit.get('status')}")

        if args.version == "v1.26.4":
            audit = loaded_reports[f"preregistered_protocol_completeness_audit_{v_norm}"]
            if audit.get("status") != "PREREGISTRATION_PROTOCOL_COMPLETE_WITH_TIE_BREAK_WARNING":
                issues.append(f"Completeness audit failed for V1.26.4: {audit.get('status')}")

        if args.version == "v1.26.6":
            archive = loaded_reports[f"preregistration_archive_integrity_{v_norm}"]
            if archive.get("archive_integrity_status") not in ["PREREGISTRATION_ARCHIVE_CLEAN", "PREREGISTRATION_ARCHIVE_HAS_SUPERSEDED_INCONSISTENCIES"]:
                issues.append(f"Archive integrity audit failed: {archive.get('archive_integrity_status')}")
            
            protocol = loaded_reports[f"preregistered_signal_validation_protocol_{v_norm}"]
            if not protocol.get("reference_protocol"):
                issues.append("V1.26.6 must be declared as reference_protocol")
            if "v1.26.2" not in protocol.get("supersedes", []):
                issues.append("V1.26.6 must supersede V1.26.2")

        # Check recommendation
        reco_key = f"v{v_norm}_recommendation" if args.version == "v1.26.3" else f"{v_norm}_recommendation"
        reco = loaded_reports[reco_key]
        if reco.get("ready_for_reviewer"):
            issues.append("Ready for reviewer should be false")
        if reco.get("holdout_executed"):
            issues.append("Holdout executed should be false")
        if not reco.get("no_real_trading"):
            issues.append("No real trading should be true")

    if args.version == "v1.26.3":
        if not issues:
            status = "PREREGISTRATION_REPORTS_CONSISTENT_COMPLETE"
        else:
            status = "PREREGISTRATION_REPORTS_INCONSISTENT"
    elif args.version == "v1.26.6":
        if not issues:
            status = "PREREGISTRATION_REPORTS_CONSISTENT_COMPLETE_WITH_TIE_BREAK_WARNING_AND_ARCHIVE_NOTES"
        else:
            status = "PREREGISTRATION_REPORTS_INCONSISTENT"
    elif args.version in ["v1.26.4", "v1.26.5"]:
        if not issues:
            status = "PREREGISTRATION_REPORTS_CONSISTENT_COMPLETE_WITH_TIE_BREAK_WARNING"
        else:
            status = "PREREGISTRATION_REPORTS_INCONSISTENT"
    else:
        status = "PREREGISTRATION_REPORTS_CONSISTENT" if not issues else "PREREGISTRATION_REPORTS_INCONSISTENT"
    
    report = {
        "version": args.version,
        "status": status,
        "issues": issues,
        "required_files_checked": required_stems
    }
    
    save_signal_report(f"preregistration_{v_norm}_consistency_check", report)
    print(f"--- Preregistration Validation {args.version}: {status} ---")
    if issues:
        for issue in issues:
            print(f"  - {issue}")

if __name__ == "__main__":
    main()
