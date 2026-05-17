from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Validate Causal Audit Reports Consistency (V1.28.1)")
    parser.add_argument("--version", default="v1.28.1")
    args = parser.parse_args()

    v_norm = args.version.lower().replace(".", "_")
    base_path = Path("reports/research")
    
    reports = {
        "static": base_path / f"causal_rule_static_audit_{v_norm}.json",
        "executability": base_path / f"live_executability_audit_{v_norm}.json",
        "verdict": base_path / f"causal_executability_verdict_{v_norm}.json",
        "recommendation": base_path / f"{v_norm}_recommendation.json"
    }

    errors = []
    
    # Load all reports
    data = {}
    for name, path in reports.items():
        if not path.exists():
            errors.append(f"Missing report: {path}")
            continue
        with open(path) as f:
            data[name] = json.load(f)

    if errors:
        print("\n".join(errors))
        sys.exit(1)

    # 1. Check Static Audit
    static = data["static"]
    if static.get("static_causality_status") != "NON_CAUSAL_FULL_PERIOD_SELECTION":
        errors.append(f"Inconsistent static_causality_status: {static.get('static_causality_status')}")

    # 2. Check Live Executability
    exec_audit = data["executability"]
    if exec_audit.get("classification") == "LIVE_EXECUTABLE":
        errors.append("Inconsistent live classification: LIVE_EXECUTABLE")

    # 3. Check Verdict
    verdict = data["verdict"]
    if "NON_CAUSAL" not in verdict.get("final_verdict", ""):
        errors.append(f"Inconsistent final_verdict: {verdict.get('final_verdict')}")

    # 4. Check Recommendation
    reco = data["recommendation"]
    if not reco.get("do_not_use_for_live_forward_validation"):
        errors.append("Recommendation fails to block live forward validation")
    if reco.get("ready_for_reviewer"):
        errors.append("ready_for_reviewer must be false")
    if reco.get("no_real_trading") is not True:
        errors.append("no_real_trading must be true")

    if errors:
        print("Consistency check FAILED:")
        print("\n".join(errors))
        
        consistency_res = {
            "status": "CAUSAL_AUDIT_REPORTS_INCONSISTENT",
            "errors": errors
        }
    else:
        print("Consistency check PASSED.")
        consistency_res = {
            "status": "CAUSAL_AUDIT_REPORTS_CONSISTENT_NON_CAUSAL",
            "version": args.version
        }

    # Save consistency report
    json_path = base_path / f"causal_audit_consistency_check_{v_norm}.json"
    with open(json_path, "w") as f:
        json.dump(consistency_res, f, indent=2)
        
    md_path = base_path / f"causal_audit_consistency_check_{v_norm}.md"
    with open(md_path, "w") as f:
        f.write(f"# Causal Audit Consistency Check ({args.version})\n\n")
        f.write(f"Status: {consistency_res['status']}\n\n")
        if errors:
            f.write("## Errors\n")
            for e in errors:
                f.write(f"- {e}\n")
        f.write("\n```json\n")
        f.write(json.dumps(consistency_res, indent=2))
        f.write("\n```\n")

    if errors:
        sys.exit(1)

if __name__ == "__main__":
    main()
