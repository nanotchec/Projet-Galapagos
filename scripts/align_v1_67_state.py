import json
from pathlib import Path

def align():
    root = Path(".")
    summary_p = root / "reports/research/microstructure_controlled_collection_summary_v1_67.json"
    state_p = root / "reports/PROJECT_STATE.json"
    metrics_p = root / "reports/current/latest_metrics.json"

    with open(summary_p) as f:
        summary = json.load(f)

    with open(state_p) as f:
        state = json.load(f)

    with open(metrics_p) as f:
        metrics = json.load(f)

    # Sync fields
    for target in [state, metrics]:
        for k, v in summary.items():
            target[k] = v

    with open(state_p, "w") as f:
        json.dump(state, f, indent=2)

    with open(metrics_p, "w") as f:
        json.dump(metrics, f, indent=2)

    print("State and metrics aligned.")

if __name__ == "__main__":
    align()
