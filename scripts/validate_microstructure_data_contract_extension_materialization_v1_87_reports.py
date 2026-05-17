import argparse
import sys
import json
from pathlib import Path
from galapagos.research.microstructure_data_contract_extension_materialization import Validator

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    if args.version != "v1_87":
        print(f"Error: Version {args.version} not supported.")
        sys.exit(1)

    validator = Validator()

    try:
        # Load reports
        summary_path = Path("reports/research/microstructure_data_contract_extension_materialization_summary_v1_87.json")
        metrics_path = Path("reports/current/latest_metrics.json")
        project_state_path = Path("reports/PROJECT_STATE.json")

        if not summary_path.exists():
            print(f"Error: Summary report missing at {summary_path}")
            sys.exit(1)

        with open(summary_path, "r") as f:
            summary_data = json.load(f)
        with open(metrics_path, "r") as f:
            metrics_data = json.load(f)
        with open(project_state_path, "r") as f:
            project_state = json.load(f)

        passed, reason = validator.validate(summary_data, metrics_data, project_state)
        
        if not passed:
            print(f"Validation FAILED: {reason}")
            sys.exit(1)

        print("V1.87 Validation PASSED successfully.")

    except Exception as e:
        print(f"Error during V1.87 validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
