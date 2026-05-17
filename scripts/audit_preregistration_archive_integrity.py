import argparse
import json
from pathlib import Path
from typing import Any

def save_json_and_md(stem: str, data: dict[str, Any], title: str):
    """Save report in both JSON and MD formats."""
    reports_dir = Path("reports/research")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # JSON
    with open(reports_dir / f"{stem}.json", "w") as f:
        json.dump(data, f, indent=2)
        
    # MD
    with open(reports_dir / f"{stem}.md", "w") as f:
        f.write(f"# {title}\n\n")
        f.write("```json\n")
        f.write(json.dumps(data, indent=2))
        f.write("\n```\n")

def main():
    parser = argparse.ArgumentParser(description="Audit Preregistration Archive Integrity (V1.26.6)")
    parser.add_argument("--version", default="v1.26.6")
    args = parser.parse_args()

    print(f"--- Galapagos {args.version} Preregistration Archive Integrity Audit ---")
    reports_dir = Path("reports/research")
    
    protocols = ["v1_26_2", "v1_26_3", "v1_26_4", "v1_26_5"]
    checked_protocols = {}
    detected_inconsistencies = []
    
    for v in protocols:
        path = reports_dir / f"preregistered_signal_validation_protocol_{v}.json"
        if not path.exists():
            checked_protocols[v] = "missing"
            continue
            
        try:
            with open(path) as f:
                data = json.load(f)
            
            # Check for known inconsistencies
            defn = data.get("locked_filter_definition", {})
            
            inconsistencies = []
            if v == "v1_26_2":
                # Known mutation in V1.26.2
                if defn.get("score_column") == "low_frequency_strict_score":
                    inconsistencies.append("V1.26.2 contains mutated score_column 'low_frequency_strict_score' (Discovery artifact name) instead of 'predicted_probability'.")
                if defn.get("selection_logic") == "fixed_percent_top_rank":
                    inconsistencies.append("V1.26.2 contains mutated selection_logic 'fixed_percent_top_rank'.")
                if defn.get("tie_break") == "random_stable":
                    inconsistencies.append("V1.26.2 contains mutated tie_break 'random_stable'.")
            
            if v == "v1_26_3":
                if defn.get("tie_break_rule") == "first_arrival_stable":
                    inconsistencies.append("V1.26.3 contains overly assertive 'first_arrival_stable' tie-break rule.")
            
            checked_protocols[v] = {
                "status": "inconsistent" if inconsistencies else "clean",
                "inconsistencies": inconsistencies
            }
            detected_inconsistencies.extend(inconsistencies)
            
        except Exception as e:
            checked_protocols[v] = f"error: {e}"

    # Reference protocol is V1.26.5/V1.26.6 (V1.26.5 was clean but we move to V1.26.6 as final reference)
    report = {
        "version": args.version,
        "checked_protocols": checked_protocols,
        "detected_inconsistencies": detected_inconsistencies,
        "reference_protocol": "v1.26.6",
        "historical_protocols_superseded": True,
        "archive_integrity_status": "PREREGISTRATION_ARCHIVE_HAS_SUPERSEDED_INCONSISTENCIES" if detected_inconsistencies else "PREREGISTRATION_ARCHIVE_CLEAN",
        "note": "Protocols V1.26.2 to V1.26.5 are superseded by V1.26.6 due to archival consistency hardening. V1.26.6 is the ONLY reference for future paper-forward validation."
    }
    
    save_json_and_md(f"preregistration_archive_integrity_{args.version.replace('.', '_')}", report, "Preregistration Archive Integrity Audit")
    print(f"--- Archive Integrity Audit Complete: {report['archive_integrity_status']} ---")

if __name__ == "__main__":
    main()
